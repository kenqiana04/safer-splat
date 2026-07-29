// Task-owned, deterministic float64 oracle backend.  It never modifies the
// official mesh and is used only for independent evaluation and route freezing.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <sstream>
#include <string>
#include <vector>

constexpr double EPS = 1e-12;

struct V {
  double x, y, z;
  V() : x(0), y(0), z(0) {}
  V(double a, double b, double c) : x(a), y(b), z(c) {}
  V operator+(const V& o) const { return {x + o.x, y + o.y, z + o.z}; }
  V operator-(const V& o) const { return {x - o.x, y - o.y, z - o.z}; }
  V operator*(double s) const { return {x * s, y * s, z * s}; }
  V operator/(double s) const { return {x / s, y / s, z / s}; }
};
static double dot(const V& a, const V& b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
static V cross(const V& a, const V& b) {
  return {a.y*b.z-a.z*b.y, a.z*b.x-a.x*b.z, a.x*b.y-a.y*b.x};
}
static double norm2(const V& a) { return dot(a, a); }

struct Box {
  V lo, hi;
  Box() : lo(std::numeric_limits<double>::infinity(), std::numeric_limits<double>::infinity(), std::numeric_limits<double>::infinity()),
          hi(-std::numeric_limits<double>::infinity(), -std::numeric_limits<double>::infinity(), -std::numeric_limits<double>::infinity()) {}
  void add(const V& p) {
    lo.x=std::min(lo.x,p.x); lo.y=std::min(lo.y,p.y); lo.z=std::min(lo.z,p.z);
    hi.x=std::max(hi.x,p.x); hi.y=std::max(hi.y,p.y); hi.z=std::max(hi.z,p.z);
  }
  void add(const Box& b) { add(b.lo); add(b.hi); }
};

struct Tri { int a, b, c; };
struct Node { Box box; int left=-1, right=-1, begin=0, count=0; bool leaf() const { return count>0; } };

static double point_box2(const V& p, const Box& b) {
  double out=0;
  const double q[3]={p.x,p.y,p.z}, lo[3]={b.lo.x,b.lo.y,b.lo.z}, hi[3]={b.hi.x,b.hi.y,b.hi.z};
  for (int i=0;i<3;i++) { if(q[i]<lo[i]) out+=(lo[i]-q[i])*(lo[i]-q[i]); else if(q[i]>hi[i]) out+=(q[i]-hi[i])*(q[i]-hi[i]); }
  return out;
}

static V closest_point_segment(const V& p, const V& a, const V& b) {
  V ab=b-a; double d=norm2(ab); if (d<=EPS) return a;
  double t=std::max(0.0,std::min(1.0,dot(p-a,ab)/d)); return a+ab*t;
}

static double segment_segment2(const V& p1, const V& q1, const V& p2, const V& q2) {
  V d1=q1-p1, d2=q2-p2, r=p1-p2; double a=dot(d1,d1), e=dot(d2,d2), f=dot(d2,r);
  double s=0,t=0;
  if(a<=EPS && e<=EPS) return norm2(p1-p2);
  if(a<=EPS) { t=std::max(0.0,std::min(1.0,f/e)); }
  else { double c=dot(d1,r); if(e<=EPS) s=std::max(0.0,std::min(1.0,-c/a));
    else { double b=dot(d1,d2), denom=a*e-b*b; if(denom!=0) s=std::max(0.0,std::min(1.0,(b*f-c*e)/denom));
      double tnom=b*s+f; if(tnom<0){t=0;s=std::max(0.0,std::min(1.0,-c/a));}
      else if(tnom>e){t=1;s=std::max(0.0,std::min(1.0,(b-c)/a));} else t=tnom/e; }
  }
  return norm2((p1+d1*s)-(p2+d2*t));
}

static V closest_point_triangle(const V& p, const V& a, const V& b, const V& c) {
  V ab=b-a, ac=c-a, ap=p-a; V n=cross(ab,ac);
  if(norm2(n)<=EPS) {
    V q=closest_point_segment(p,a,b), r=closest_point_segment(p,b,c), s=closest_point_segment(p,c,a);
    double dq=norm2(p-q), dr=norm2(p-r), ds=norm2(p-s); return dq<=dr && dq<=ds?q:(dr<=ds?r:s);
  }
  double d1=dot(ab,ap), d2=dot(ac,ap); if(d1<=0 && d2<=0) return a;
  V bp=p-b; double d3=dot(ab,bp), d4=dot(ac,bp); if(d3>=0 && d4<=d3) return b;
  double vc=d1*d4-d3*d2; if(vc<=0 && d1>=0 && d3<=0) { double v=d1/(d1-d3); return a+ab*v; }
  V cp=p-c; double d5=dot(ab,cp), d6=dot(ac,cp); if(d6>=0 && d5<=d6) return c;
  double vb=d5*d2-d1*d6; if(vb<=0 && d2>=0 && d6<=0) { double w=d2/(d2-d6); return a+ac*w; }
  double va=d3*d6-d5*d4; if(va<=0 && (d4-d3)>=0 && (d5-d6)>=0) { V bc=c-b; double w=(d4-d3)/((d4-d3)+(d5-d6)); return b+bc*w; }
  double den=1.0/(va+vb+vc); double v=vb*den,w=vc*den; return a+ab*v+ac*w;
}

static bool segment_triangle_intersects(const V& p, const V& q, const V& a, const V& b, const V& c) {
  V d=q-p,e1=b-a,e2=c-a,h=cross(d,e2); double det=dot(e1,h);
  if(std::abs(det)<EPS) return false;
  double inv=1.0/det; V s=p-a; double u=inv*dot(s,h); if(u<-EPS||u>1+EPS) return false;
  V r=cross(s,e1); double v=inv*dot(d,r); if(v<-EPS||u+v>1+EPS) return false;
  double t=inv*dot(e2,r); return t>=-EPS && t<=1+EPS;
}

static double segment_triangle2(const V& p, const V& q, const V& a, const V& b, const V& c) {
  if(segment_triangle_intersects(p,q,a,b,c)) return 0.0;
  double best=norm2(p-closest_point_triangle(p,a,b,c));
  best=std::min(best,norm2(q-closest_point_triangle(q,a,b,c)));
  best=std::min(best,segment_segment2(p,q,a,b)); best=std::min(best,segment_segment2(p,q,b,c)); best=std::min(best,segment_segment2(p,q,c,a));
  return best;
}

// Exact squared distance from a segment to a closed AABB by minimizing the
// piecewise quadratic point-to-box distance over t in [0,1].
static double segment_box2(const V& a, const V& b, const Box& box) {
  V d=b-a; std::vector<double> cuts={0.0,1.0};
  const double av[3]={a.x,a.y,a.z}, dv[3]={d.x,d.y,d.z}, lo[3]={box.lo.x,box.lo.y,box.lo.z}, hi[3]={box.hi.x,box.hi.y,box.hi.z};
  for(int i=0;i<3;i++) if(std::abs(dv[i])>EPS) { for(double z:{lo[i],hi[i]}) { double t=(z-av[i])/dv[i]; if(t>0&&t<1) cuts.push_back(t); } }
  std::sort(cuts.begin(),cuts.end()); cuts.erase(std::unique(cuts.begin(),cuts.end()),cuts.end());
  auto eval=[&](double t){return point_box2(a+d*t,box);}; double best=std::numeric_limits<double>::infinity();
  for(size_t k=0;k+1<cuts.size();k++) { double l=cuts[k],r=cuts[k+1],m=0.5*(l+r),aa=0,bb=0;
    for(int i=0;i<3;i++) { double v=av[i]+m*dv[i], bound=0; bool active=false; if(v<lo[i]){bound=lo[i];active=true;} else if(v>hi[i]){bound=hi[i];active=true;} if(active){double c=av[i]-bound;aa+=dv[i]*dv[i];bb+=dv[i]*c;} }
    best=std::min(best,eval(l)); best=std::min(best,eval(r)); if(aa>EPS){double t=std::max(l,std::min(r,-bb/aa));best=std::min(best,eval(t));}
  }
  return best;
}

struct MeshOracle {
  std::vector<V> v; std::vector<Tri> f; std::vector<Box> tri_box; std::vector<V> cent; std::vector<int> order; std::vector<Node> nodes;
  Box triangle_box(int id) const { return tri_box[id]; }
  void load(const std::string& path) {
    std::ifstream in(path,std::ios::binary); if(!in) throw std::runtime_error("cannot open mesh");
    std::string line; size_t nv=0,nf=0; while(std::getline(in,line)) { if(line.rfind("element vertex ",0)==0) nv=std::stoull(line.substr(15)); else if(line.rfind("element face ",0)==0) nf=std::stoull(line.substr(13)); else if(line=="end_header") break; }
    if(nv==0||nf==0) throw std::runtime_error("invalid PLY header"); v.reserve(nv);
    for(size_t i=0;i<nv;i++){float x,y,z,nx,ny,nz;uint8_t r,g,b;in.read((char*)&x,4);in.read((char*)&y,4);in.read((char*)&z,4);in.read((char*)&nx,4);in.read((char*)&ny,4);in.read((char*)&nz,4);in.read((char*)&r,1);in.read((char*)&g,1);in.read((char*)&b,1);v.emplace_back(x,y,z);}
    f.reserve(nf); for(size_t i=0;i<nf;i++){uint8_t n;in.read((char*)&n,1);std::vector<uint32_t> q(n);for(uint8_t j=0;j<n;j++)in.read((char*)&q[j],4);for(uint8_t j=1;j+1<n;j++)f.push_back({(int)q[0],(int)q[j],(int)q[j+1]});}
    tri_box.resize(f.size());cent.resize(f.size());order.resize(f.size()); for(size_t i=0;i<f.size();i++){auto t=f[i];Box b;b.add(v[t.a]);b.add(v[t.b]);b.add(v[t.c]);tri_box[i]=b;cent[i]=(v[t.a]+v[t.b]+v[t.c])/3.0;order[i]=(int)i;}
    nodes.reserve(f.size()/4); build(0,(int)f.size());
  }
  int build(int begin,int end){Node n;Box cb;for(int i=begin;i<end;i++){n.box.add(tri_box[order[i]]);cb.add(cent[order[i]]);}int id=(int)nodes.size();nodes.push_back(n);int count=end-begin;if(count<=12){nodes[id].begin=begin;nodes[id].count=count;return id;}V ex=cb.hi-cb.lo;int axis=(ex.y>ex.x?1:0);if((axis==0?ex.z:ex.z)>(axis==0?ex.x:ex.y))axis=2;int mid=(begin+end)/2;auto coord=[&](int tid){return axis==0?cent[tid].x:(axis==1?cent[tid].y:cent[tid].z);};std::nth_element(order.begin()+begin,order.begin()+mid,order.begin()+end,[&](int a,int b){double ca=coord(a),cb=coord(b);return ca==cb?a<b:ca<cb;});int l=build(begin,mid),r=build(mid,end);nodes[id].left=l;nodes[id].right=r;return id;}
  struct Result { double d; V q; int tri; };
  Result point(const V& p,bool brute=false) const {double best=std::numeric_limits<double>::infinity();V bestq;int bestid=-1; auto consider=[&](int id){auto t=f[id];V q=closest_point_triangle(p,v[t.a],v[t.b],v[t.c]);double d=norm2(p-q);if(d<best){best=d;bestq=q;bestid=id;}}; if(brute){for(size_t i=0;i<f.size();i++)consider((int)i);}else{using Q=std::pair<double,int>;std::priority_queue<Q,std::vector<Q>,std::greater<Q>> pq;pq.push({0,0});while(!pq.empty()){auto [lb,id]=pq.top();pq.pop();if(lb>best)continue;auto &n=nodes[id];if(n.leaf())for(int i=n.begin;i<n.begin+n.count;i++)consider(order[i]);else{pq.push({point_box2(p,nodes[n.left].box),n.left});pq.push({point_box2(p,nodes[n.right].box),n.right});}}}return {std::sqrt(best),bestq,bestid};}
  Result segment(const V& a,const V& b,bool brute=false) const {double best=std::numeric_limits<double>::infinity();int bestid=-1;auto consider=[&](int id){auto t=f[id];double d=segment_triangle2(a,b,v[t.a],v[t.b],v[t.c]);if(d<best){best=d;bestid=id;}};if(brute){for(size_t i=0;i<f.size();i++)consider((int)i);}else{using Q=std::pair<double,int>;std::priority_queue<Q,std::vector<Q>,std::greater<Q>> pq;pq.push({0,0});while(!pq.empty()){auto [lb,id]=pq.top();pq.pop();if(lb>best)continue;auto &n=nodes[id];if(n.leaf())for(int i=n.begin;i<n.begin+n.count;i++)consider(order[i]);else{pq.push({segment_box2(a,b,nodes[n.left].box),n.left});pq.push({segment_box2(a,b,nodes[n.right].box),n.right});}}}return {std::sqrt(best),V(),bestid};}
};

int main(int argc,char** argv){if(argc<4){std::cerr<<"usage: oracle mesh.ply queries.txt result.txt [--bruteforce]\n";return 2;}try{MeshOracle o;o.load(argv[1]);bool brute=argc>4&&std::string(argv[4])=="--bruteforce";std::ifstream in(argv[2]);std::ofstream out(argv[3]);if(!in||!out)throw std::runtime_error("query/result open failure");out<<std::setprecision(17);std::string type;while(in>>type){if(type=="P"){V p;in>>p.x>>p.y>>p.z;auto a=o.point(p,false);double bd=-1;if(brute)bd=o.point(p,true).d;out<<"P "<<a.d<<" "<<a.q.x<<" "<<a.q.y<<" "<<a.q.z<<" "<<a.tri<<" "<<bd<<" "<<(bd<0?-1:std::abs(a.d-bd))<<"\n";}else if(type=="S"){V a,b;in>>a.x>>a.y>>a.z>>b.x>>b.y>>b.z;auto q=o.segment(a,b,false);double bd=-1;if(brute)bd=o.segment(a,b,true).d;out<<"S "<<q.d<<" 0 0 0 "<<q.tri<<" "<<bd<<" "<<(bd<0?-1:std::abs(q.d-bd))<<"\n";}else throw std::runtime_error("bad query type");}std::cerr<<"vertices="<<o.v.size()<<" triangles="<<o.f.size()<<" nodes="<<o.nodes.size()<<"\n";}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}return 0;}
