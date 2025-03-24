from typing import Optional, Dict, Literal, Set

from pathlib import Path
import numpy as np
import trimesh
import rclpy
from std_msgs.msg import Float32MultiArray

import viser
import viser.theme
import viser.transforms as vtf
from nerfstudio.viewer.viewer import Viewer
from nerfstudio.data.datasets.base_dataset import InputDataset

VISER_NERFSTUDIO_SCALE_RATIO: float = 10.0


class ROSViewer(Viewer):
    """
    A viewer that supports rendering streaming training views.
    """

    def init_scene(
        self,
        train_dataset: InputDataset,
        train_state: Literal["training", "paused", "completed"],
        eval_dataset: Optional[InputDataset] = None,
    ) -> None:
        """Draw some images and the scene aabb in the viewer.

        Args:
            dataset: dataset to render in the scene
            train_state: Current status of training
        """
        # draw the training cameras and images
        self.camera_handles: Dict[int, viser.CameraFrustumHandle] = {}
        self.original_c2w: Dict[int, np.ndarray] = {}
        self.cameras_drawn: Set[int] = set()
        self.dataset = train_dataset
        image_indices = self._pick_drawn_image_idxs(len(train_dataset))
        cameras = train_dataset.cameras.to("cpu")
        for idx in image_indices:
            camera = cameras[idx]
            c2w = camera.camera_to_worlds.cpu().numpy()
            R = vtf.SO3.from_matrix(c2w[:3, :3])
            R = R @ vtf.SO3.from_x_radians(np.pi)
            camera_handle = self.viser_server.add_camera_frustum(
                name=f"/cameras/camera_{idx:05d}",
                fov=float(2 * np.arctan(camera.cx / camera.fx[0])),
                scale=self.config.camera_frustum_scale,
                aspect=float(camera.cx[0] / camera.cy[0]),
                image=None,
                wxyz=R.wxyz,
                position=c2w[:3, 3] * VISER_NERFSTUDIO_SCALE_RATIO,
                visible=False,
            )

            @camera_handle.on_click
            def _(
                event: viser.SceneNodePointerEvent[viser.CameraFrustumHandle],
            ) -> None:
                with event.client.atomic():
                    event.client.camera.position = event.target.position
                    event.client.camera.wxyz = event.target.wxyz

            self.camera_handles[idx] = camera_handle
            self.original_c2w[idx] = c2w

        self.train_state = train_state
        self.train_util = 0.9
        self.acc_vis_threshold = 0.15

    def setup_robot_viewer_node(self):
        """Returns the viewer node for the scene.

        Args:
            mode: replay or live mode
        Returns:
            The viewer node for the scene
        """
        self.init_robot_mesh()
        self.node = rclpy.create_node("viser_state_node")
        self.desired_control_sub = self.node.create_subscription(
            Float32MultiArray, "/cbf_desired", self.cbf_des_callback, 3
        )
        self.optimal_control_sub = self.node.create_subscription(
            Float32MultiArray, "/cbf_optimal", self.cbf_opt_callback, 3
        )
        self.robot_position = np.zeros(3)

    def cbf_des_callback(self, msg: Float32MultiArray):
        """
        This also contains the current robot state so we can update the
        robot pose also.
        """
        px, py, pz, yaw = msg.data[6], msg.data[7], msg.data[8], msg.data[9]
        acc = np.array([msg.data[0], msg.data[1], msg.data[2]])
        position = np.array([px, py, pz]) * VISER_NERFSTUDIO_SCALE_RATIO
        self.robot_position = position
        rot = (
            vtf.SO3.from_z_radians(yaw)
            @ vtf.SO3.from_x_radians(np.pi)
            @ vtf.SO3.from_z_radians(np.pi / 2)
        )
        self.robot_handle.position = position
        self.robot_handle.wxyz = rot.wxyz
        self.des_control_handle.position = position
        self.opt_control_handle.position = position
        mag_des, rot_des = self.get_rotatation_from_acc(acc)
        rot = vtf.SO3.from_matrix(rot_des)
        if mag_des > self.acc_vis_threshold:
            self.des_control_handle.visible = True
        else:
            self.des_control_handle.visible = False
        self.des_control_handle.wxyz = rot.wxyz

    def cbf_opt_callback(self, msg: Float32MultiArray):
        acc = np.array([msg.data[0], msg.data[1], msg.data[2]])
        mag_opt, rot_opt = self.get_rotatation_from_acc(acc)
        rot = vtf.SO3.from_matrix(rot_opt)
        if mag_opt > self.acc_vis_threshold:
            self.opt_control_handle.visible = True
        else:
            self.opt_control_handle.visible = False
        self.opt_control_handle.wxyz = rot.wxyz

    def get_rotatation_from_acc(self, acc: np.ndarray) -> np.ndarray:
        v2 = np.array([1, 0, 0])
        mag = np.linalg.norm(acc)
        if mag == 0:
            return mag, np.identity(3)
        acc = acc / mag
        cross_prod = np.cross(acc, v2)
        sin_theta = np.linalg.norm(cross_prod)
        cos_theta = np.dot(acc, v2)
        # Normalize the rotation axis
        k = cross_prod / sin_theta
        # Skew-symmetric cross-product matrix of k
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        # Rotation matrix using Rodrigues' rotation formula
        R = np.identity(3) + K * sin_theta + np.dot(K, K) * (1 - cos_theta)
        return mag, R.T


    def init_robot_mesh(self) -> None:
        """Draw the robot mesh in the scene.

        Args:
            robot_mesh: path to the robot mesh
        """
        mesh_path = str(Path(__file__).parent.parent / "meshes/drone.obj")
        mesh = trimesh.load_mesh(mesh_path)
        scale = VISER_NERFSTUDIO_SCALE_RATIO
        self.robot_handle = self.viser_server.add_mesh_trimesh(
            name="/robot",
            mesh=mesh,
            scale=scale,
            wxyz=vtf.SO3.from_x_radians(0.0).wxyz,
            position=(0.0, 0.0, 0.0),
            visible=True,
        )
        self.base_arrow_scale = 0.01 * VISER_NERFSTUDIO_SCALE_RATIO
        green_arrow = trimesh.load_mesh(
            str(Path(__file__).parent.parent / "meshes/green_arrow_x.obj")
        )
        orange_arrow = trimesh.load_mesh(
            str(Path(__file__).parent.parent / "meshes/orange_arrow_x.obj")
        )
        self.des_control_handle = self.viser_server.add_mesh_trimesh(
            name="/desired_control",
            mesh=orange_arrow,
            scale=self.base_arrow_scale,
            wxyz=vtf.SO3.from_x_radians(0.0).wxyz,
            position=(0.0, 0.0, 0.0),
            visible=True,
        )
        self.opt_control_handle = self.viser_server.add_mesh_trimesh(
            name="/optimal_control",
            mesh=green_arrow,
            scale=self.base_arrow_scale,
            wxyz=vtf.SO3.from_x_radians(0.0).wxyz,
            position=(0.0, 0.0, 0.0),
            visible=True,
        )

    def update_camera_poses(self):
        """Updates the camera poses in the scene."""
        image_indices = self.dataset.updated_indices
        for idx in image_indices:
            if (not idx in self.cameras_drawn) and (idx in self.camera_handles):
                self.original_c2w[idx] = (
                    self.dataset.cameras.camera_to_worlds[idx].cpu().numpy()
                )
                self.camera_handles[idx].visible = True
                self.cameras_drawn.add(idx)
        super().update_camera_poses()
