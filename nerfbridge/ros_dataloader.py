# Code adapted from Nerfstudio
# https://github.com/nerfstudio-project/nerfstudio/blob/df784e96e7979aaa4320284c087d7036dce67c28/nerfstudio/data/utils/dataloaders.py

"""
Defines the ROSDataloader object that subscribes to pose and images topics,
and populates an image tensor and Cameras object with values from these topics.
Image and pose pairs are added at a prescribed frequency and intermediary images
are discarded (could be used for evaluation down the line).
"""
import time
import threading
import warnings
from typing import Union, Tuple

from rich.console import Console
import torch
from torch.utils.data.dataloader import DataLoader
from rclpy.executors import MultiThreadedExecutor

import nerfbridge.pose_utils as pose_utils
from nerfbridge.ros_dataset import ROSDataset
from nerfbridge.pc2_utils import read_points

import rclpy
from sensor_msgs.msg import Image, CompressedImage
from sensor_msgs.msg import Image, PointCloud2
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from message_filters import ApproximateTimeSynchronizer, TimeSynchronizer, Subscriber
from cv_bridge import CvBridge
import cv2
import time
import numpy as np
import open3d as o3d

CONSOLE = Console(width=120)

# Suppress a warning from torch.tensorbuffer about copying that
# does not apply in this case.
warnings.filterwarnings("ignore", "The given buffer")


class ROSDataloader(DataLoader):
    """
    Creates batches of the dataset return type. In this case of nerfstudio this means
    that we are returning batches of full images, which then are sampled using a
    PixelSampler. For this class the image batches are progressively growing as
    more images are recieved from ROS, and stored in a pytorch tensor.

    Args:
        dataset: Dataset to sample from.
        data_update_freq: Frequency (wall clock) that images are added to the training
            data tensors. If this value is less than the frequency of the topics to which
            this dataloader subscribes (pose and images) then this subsamples the ROS data.
            Otherwise, if the value is larger than the ROS topic rates then every pair of
            messages is added to the training bag.
        slam_method: string that determines which type of pose topic to subscribe to and
            what coordinate transforms to use when handling the poses. Currently, only
            "cuvslam" is supported.
        topic_sync: use "exact" when your slam algorithm matches pose and image time stamps,
            and use "approx" when it does not.
        topic_slop: if using approximate time synchronization, then this float determines
            the slop in seconds that is allowable between images and poses.
        device: Device to perform computation.
    """

    dataset: ROSDataset

    def __init__(
        self,
        dataset: ROSDataset,
        data_update_freq: float,
        slam_method: str,
        topic_sync: str,
        topic_slop: float,
        use_compressed_rgb: bool,
        undistort_images: bool,
        use_depth: bool,
        use_pc: bool,
        blur_threshold: float,
        pose_reject_radius: float,
        device: Union[torch.device, str] = "cpu",
        **kwargs,
    ):
        # This is mostly a parameter placeholder, and manages the cameras
        self.dataset = dataset
        self.use_depth = use_depth
        self.use_pc = use_pc

        # Image meta data
        self.device = device
        self.num_images = len(self.dataset)
        self.H = self.dataset.image_height
        self.W = self.dataset.image_width
        self.n_channels = 3
        self.blur_threshold = blur_threshold
        self.pose_reject_radius = pose_reject_radius

        # Tracking ros updates
        self.current_idx = 0
        self.buffered_idx = 0
        self.updated = True
        self.update_period = 1 / data_update_freq

        self.pose_buffer = []

        # Keep it in the format so that it makes it look more like a
        # regular data loader.
        self.data_dict = {
            "image": self.dataset.image_tensor,
            "image_idx": self.dataset.image_indices,
        }

        # Flag for depth training, add depth tensor to data.
        if use_depth:
            self.data_dict["depth_image"] = self.dataset.depth_tensor

        super().__init__(dataset=dataset, **kwargs)

        self.bridge = CvBridge()
        self.slam_method = slam_method
        self.use_compressed_rgb = use_compressed_rgb
        self.undistort_images = undistort_images
        self.K = self.dataset.K.numpy()
        self.dparams = self.dataset.dparams.numpy()

        # Initializing ROS2
        self.node = rclpy.create_node("nerf_bridge_node")

        self.last_update_t = time.perf_counter()

        self.subs = []
        self.subs.append(
            Subscriber(
                self.node,
                CompressedImage if self.use_compressed_rgb else Image,
                self.dataset.image_topic_name,
            )
        )

        if slam_method == "cuvslam":
            self.subs.append(
                Subscriber(self.node, Odometry, self.dataset.pose_topic_name)
            )
        elif slam_method == "orbslam3":
            self.subs.append(
                Subscriber(self.node, PoseStamped, self.dataset.pose_topic_name)
            )
        elif slam_method == "mocap":
            self.subs.append(
                Subscriber(self.node, PoseStamped, self.dataset.pose_topic_name)
            )
        elif self.slam_method == "zedsdk":
            self.subs.append(
                Subscriber(self.node, PoseStamped, self.dataset.pose_topic_name)
            )
        elif self.slam_method == "modal":
            self.subs.append(
                Subscriber(self.node, PoseStamped, self.dataset.pose_topic_name)
            )
        else:
            raise NameError(
                "Unsupported SLAM algorithm. Must be one of {cuvslam, orbslam3}"
            )

        assert not (self.use_depth and self.use_pc), "Cannot use both depth and pc"
        if self.use_depth:
            self.subs.append(
                Subscriber(self.node, Image, self.dataset.depth_topic_name)
            )
        if self.use_pc:
            self.subs.append(
                Subscriber(self.node, PointCloud2, self.dataset.pc_topic_name)
            )

        if topic_sync == "approx":
            self.ts = ApproximateTimeSynchronizer(self.subs, 40, topic_slop)
        elif topic_sync == "exact":
            self.ts = TimeSynchronizer(self.subs, 40)
        else:
            raise NameError("Unsupported topic sync method. Must be {approx, exact}.")

        self.ts.registerCallback(self.ts_callback)

        # Create a multi-threaded executor to spin both nodes
        self.executor = MultiThreadedExecutor()
        # Add both the dataloader node and the new cbf node to the executor
        self.executor.add_node(self.node)

    def start_ros_thread(self):
        self.ros_thread = threading.Thread(target=self.executor.spin, daemon=True)
        self.ros_thread.start()

    def ts_callback(self, *args):
        last_t = self.last_update_t

        now = time.perf_counter()
        if now - last_t > self.update_period and self.current_idx < self.num_images:
            # Process RGB and Pose
            im_success, rgb = self.image_callback(args[0])
            pose_success, pose = self.pose_callback(args[1])

            success = im_success and pose_success

            # Process Depth if using depth training
            if self.use_depth:
                d_success, depth = self.depth_callback(args[2])
                success = success and d_success

            if self.use_pc:
                pc = self.pointcloud_callback(args[2])

                # transform the point cloud into the RBG camera frame below
                # self.rotation_matrix = np.array(
                #     [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
                # )
                # self.translation_vector = np.array([0.016, -0.013, 0.025])
                # R = self.dataset.pc2c[:3, :3]
                # trans = self.dataset.pc2c[:3, 3]
                # transformed_points = (R @ pc.T).T + trans

            if success:
                # Insert image
                self.dataset.image_tensor[self.current_idx] = rgb

                # Add pose to buffer instead
                self.pose_buffer.append((self.current_idx, pose))

                # Insert depth
                if self.use_depth:
                    self.dataset.depth_tensor[self.current_idx] = depth

                if self.use_pc:
                    self.dataset.pc_dict[self.current_idx] = pc
            else:
                # Skip this frame
                return

            # self.dataset.updated_indices.append(self.current_idx)
            self.updated = True
            self.current_idx += 1
            self.last_update_t = now

    def image_callback(
        self, image: Image | CompressedImage
    ) -> Tuple[bool, torch.Tensor]:
        """
        Callback for processing RGB Image Messages, and adding them to the
        dataset for training.
        """
        # Load the image message directly into the torch
        if self.use_compressed_rgb:
            im_cv = self.bridge.compressed_imgmsg_to_cv2(image)
            im_cv = cv2.cvtColor(im_cv, cv2.COLOR_BGR2RGB)
        else:
            im_cv = self.bridge.imgmsg_to_cv2(image, image.encoding)
            if self.slam_method == "modal":
                im_cv = cv2.cvtColor(im_cv, cv2.COLOR_YUV2RGB_Y422)
            else:
                im_cv = cv2.cvtColor(im_cv, cv2.COLOR_BGR2RGB)

        if self.undistort_images:
            im_cv = cv2.undistort(im_cv, self.K, self.dparams, None, None)

        # Filter motion blur
        if self.blur_threshold > 0:
            laplacian = cv2.Laplacian(im_cv, cv2.CV_64F).var()
            if laplacian < self.blur_threshold:
                return False, None

        im_tensor = torch.from_numpy(im_cv).to(dtype=torch.float32) / 255.0
        return True, im_tensor

    def pose_callback(self, pose: PoseStamped | Odometry) -> Tuple[bool, torch.Tensor]:
        """
        Callback for Pose messages. Extracts pose, converts it to Nerfstudio coordinate
        convention, and inserts it into the Cameras object.
        """
        if self.slam_method == "cuvslam":
            # Odometry Message
            hom_pose = pose_utils.ros_pose_to_homogenous(pose.pose)
            c2w = pose_utils.cuvslam_to_nerfstudio(hom_pose)
        elif self.slam_method == "orbslam3":
            # PoseStamped Message
            hom_pose = pose_utils.ros_pose_to_homogenous(pose)
            c2w = pose_utils.orbslam3_to_nerfstudio(hom_pose)
        elif self.slam_method == "mocap":
            # PoseStamped Message
            hom_pose = pose_utils.ros_pose_to_homogenous(pose)
            c2w = pose_utils.mocap_to_nerfstudio(hom_pose)
        elif self.slam_method == "zedsdk":
            # Odometry Message
            hom_pose = pose_utils.ros_pose_to_homogenous(pose)
            c2w = pose_utils.cuvslam_to_nerfstudio(hom_pose)
        elif self.slam_method == "modal":
            # PoseStamped Message
            hom_pose = pose_utils.ros_pose_to_homogenous(pose)
            self.ros_pose = hom_pose
            hom_pose = hom_pose @ self.dataset.pose2c
            c2w = pose_utils.opencv_to_nerfstudio(hom_pose)
        else:
            raise NameError("Unknown SLAM Method!")

        # Scale Pose to nerf size
        c2w[:3, 3] *= self.dataset.scene_scale_factor
        device = self.dataset.cameras.device
        c2w = c2w.to(device)

        if self.current_idx > 0:
            if len(self.pose_buffer) > 0:
                prev_pos = self.pose_buffer[-1][1][:3, 3]
            else:
                all_c2ws = self.dataset.cameras.camera_to_worlds
                prev_pos = all_c2ws[self.buffered_idx][:3, 3]
            dist = torch.norm(c2w[:3, 3] - prev_pos)
            if dist < self.pose_reject_radius * self.dataset.scene_scale_factor:
                return False, None
        return True, c2w

    def pointcloud_callback(self, pc_msg):
        pcd_as_numpy_array = np.array(list(read_points(pc_msg)))
        pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pcd_as_numpy_array))
        pc_points = np.asarray(pc.points)
        R = self.dataset.pc2c[:3, :3]
        trans = self.dataset.pc2c[:3, 3]
        transformed_points = (R @ pc_points.T).T + trans
        return transformed_points

    def update_dataset_from_buffer(self, step: int):
        """
        Update the dataset's camera poses from the buffer after each training step.
        """
        with torch.no_grad():
            for idx, c2w in self.pose_buffer:
                device = self.dataset.cameras.device
                self.dataset.cameras.camera_to_worlds[idx] = c2w.to(device)
                self.dataset.updated_indices.append(idx)
                self.buffered_idx = idx
        self.pose_buffer.clear()

    def depth_callback(self, depth: Image) -> Tuple[bool, torch.Tensor]:
        """
        Callback for processing Depth Image messages. Similar to RGB image handling,
        but also rescales the depth to the appropriate value.
        """
        depth_cv = self.bridge.imgmsg_to_cv2(depth, depth.encoding)
        depth_tensor = torch.from_numpy(depth_cv.astype("float32")).to(
            dtype=torch.float32
        )
        depth_tensor = torch.nan_to_num(depth_tensor)

        aggregate_scale = (
            self.dataset.scene_scale_factor * self.dataset.depth_scale_factor
        )
        depth_tensor = depth_tensor.unsqueeze(-1) * aggregate_scale

        return True, depth_tensor

    def __getitem__(self, idx):
        return self.dataset.__getitem__(idx)

    def _get_updated_batch(self):
        batch = {}
        for k, v in self.data_dict.items():
            if isinstance(v, torch.Tensor):
                batch[k] = v[: self.current_idx, ...]
        return batch

    def __iter__(self):
        while True:
            if self.updated:
                self.batch = self._get_updated_batch()
                self.updated = False

            batch = self.batch
            yield batch
