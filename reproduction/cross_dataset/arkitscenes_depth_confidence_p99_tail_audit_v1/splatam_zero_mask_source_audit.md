# Official SplaTAM zero-valid-depth source audit

Authority: `da6bbcd24c248dc884ac7f49d62e91b841b26ccc`
File SHA-256: `b8adb286bea49d6302769ec5af25af4938318044691a8996575c443e4b538816`

## First-frame initialization

```python
190:         densify_intrinsics = densify_intrinsics[:3, :3]
191:         densify_cam = setup_camera(color.shape[2], color.shape[1], densify_intrinsics.cpu().numpy(), w2c.detach().cpu().numpy())
192:     else:
193:         densify_intrinsics = intrinsics
194:
195:     # Get Initial Point Cloud (PyTorch CUDA Tensor)
196:     mask = (depth > 0) # Mask out invalid depth values
197:     mask = mask.reshape(-1)
198:     init_pt_cld, mean3_sq_dist = get_pointcloud(color, depth, densify_intrinsics, w2c,
199:                                                 mask=mask, compute_mean_sq_dist=True,
200:                                                 mean_sq_dist_method=mean_sq_dist_method)
201:
202:     # Initialize Parameters
```

There is no official zero-count skip before the initial point cloud and parameter construction. The same function later derives `scene_radius` from the maximum depth, which is zero for an all-zero frame.

## Tracking and mapping loss

```python
260:
261:     # Mask with valid depth values (accounts for outlier depth values)
262:     nan_mask = (~torch.isnan(depth)) & (~torch.isnan(uncertainty))
263:     if ignore_outlier_depth_loss:
264:         depth_error = torch.abs(curr_data['depth'] - depth) * (curr_data['depth'] > 0)
265:         mask = (depth_error < 10*depth_error.median())
266:         mask = mask & (curr_data['depth'] > 0)
267:     else:
268:         mask = (curr_data['depth'] > 0)
269:     mask = mask & nan_mask
270:     # Mask with presence silhouette mask (accounts for empty space)
271:     if tracking and use_sil_for_loss:
272:         mask = mask & presence_sil_mask
273:
274:     # Depth loss
275:     if use_l1:
276:         mask = mask.detach()
277:         if tracking:
278:             losses['depth'] = torch.abs(curr_data['depth'] - depth)[mask].sum()
279:         else:
280:             losses['depth'] = torch.abs(curr_data['depth'] - depth)[mask].mean()
281:
282:     # RGB Loss
283:     if tracking and (use_sil_for_loss or ignore_outlier_depth_loss):
284:         color_mask = torch.tile(mask, (3, 1, 1))
285:         color_mask = color_mask.detach()
286:         losses['im'] = torch.abs(curr_data['im'] - im)[color_mask].sum()
287:     elif tracking:
288:         losses['im'] = torch.abs(curr_data['im'] - im).sum()
289:     else:
290:         losses['im'] = 0.8 * l1_loss_v1(im, curr_data['im']) + 0.2 * (1.0 - calc_ssim(im, curr_data['im']))
291:
```

Tracking uses an empty masked `sum`, which is finite zero. Mapping uses an empty masked `mean`, which is nonfinite. The RGB mapping loss is structurally independent, but it does not make the combined weighted loss finite when depth is NaN.

## New-frame densification

```python
384:     depth_sil, _, _, = Renderer(raster_settings=curr_data['cam'])(**depth_sil_rendervar)
385:     silhouette = depth_sil[1, :, :]
386:     non_presence_sil_mask = (silhouette < sil_thres)
387:     # Check for new foreground objects by using GT depth
388:     gt_depth = curr_data['depth'][0, :, :]
389:     render_depth = depth_sil[0, :, :]
390:     depth_error = torch.abs(gt_depth - render_depth) * (gt_depth > 0)
391:     non_presence_depth_mask = (render_depth > gt_depth) * (depth_error > 50*depth_error.median())
392:     # Determine non-presence mask
393:     non_presence_mask = non_presence_sil_mask | non_presence_depth_mask
394:     # Flatten mask
395:     non_presence_mask = non_presence_mask.reshape(-1)
396:
397:     # Get the new frame Gaussians based on the Silhouette
398:     if torch.sum(non_presence_mask) > 0:
399:         # Get the new pointcloud in the world frame
400:         curr_cam_rot = torch.nn.functional.normalize(params['cam_unnorm_rots'][..., time_idx].detach())
401:         curr_cam_tran = params['cam_trans'][..., time_idx].detach()
402:         curr_w2c = torch.eye(4).cuda().float()
403:         curr_w2c[:3, :3] = build_rotation(curr_cam_rot)
404:         curr_w2c[:3, 3] = curr_cam_tran
405:         valid_depth_mask = (curr_data['depth'][0, :, :] > 0)
406:         non_presence_mask = non_presence_mask & valid_depth_mask.reshape(-1)
407:         new_pt_cld, mean3_sq_dist = get_pointcloud(curr_data['im'], curr_data['depth'], curr_data['intrinsics'],
408:                                     curr_w2c, mask=non_presence_mask, compute_mean_sq_dist=True,
409:                                     mean_sq_dist_method=mean_sq_dist_method)
410:         new_params = initialize_new_params(new_pt_cld, mean3_sq_dist, gaussian_distribution)
411:         for k, v in new_params.items():
412:             params[k] = torch.nn.Parameter(torch.cat((params[k], v), dim=0).requires_grad_(True))
```

The official code intersects the non-presence mask with positive depth, but only after deciding that the pre-intersection non-presence mask is nonempty. No explicit zero-depth-frame skip establishes a safe finite mapper contract.

## Decision

`FAIL_OFFICIAL_SPLATAM_ZERO_VALID_DEPTH_COMPATIBILITY`. This is a source and forward-reduction audit only: no mapper, optimizer, backward, parameter update, or real scene execution occurred.
