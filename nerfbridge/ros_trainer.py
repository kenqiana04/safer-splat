from __future__ import annotations

import time
import dataclasses
from dataclasses import dataclass, field
from typing import Type
from typing_extensions import Literal
import struct
import threading
from rich.console import Console
from pathlib import Path
import cv2

import torch
import numpy as np
import rclpy
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header, Float32MultiArray

from nerfstudio.engine.trainer import Trainer, TrainerConfig
from nerfstudio.utils import profiler, writer
from nerfstudio.engine.callbacks import (
    TrainingCallbackAttributes,
    TrainingCallbackLocation,
    TrainingCallback,
)
from nerfbridge.ros_dataset import ROSDataset
from nerfbridge.ros_viewer import ROSViewer

CONSOLE = Console(width=90)


@dataclass
class ROSTrainerConfig(TrainerConfig):
    _target: Type = field(default_factory=lambda: ROSTrainer)
    msg_timeout: float = 300.0
    """ How long to wait (seconds) for sufficient images to be received before training. """
    num_msgs_to_start: int = 20
    """ Number of images that must be recieved before training can start. """
    enable_cbf: bool = False
    """ Whether to enable the control barrier function. """
    show_robot_cbf_in_viewer: bool = True
    """ Whether to show the robot state in the viewer. """


class ROSTrainer(Trainer):
    config: ROSTrainerConfig
    dataset: ROSDataset

    def __init__(
        self, config: ROSTrainerConfig, local_rank: int = 0, world_size: int = 0
    ):
        # We'll see if this throws and error (it expects a different config type)
        super().__init__(config, local_rank=local_rank, world_size=world_size)
        self.msg_timeout = self.config.msg_timeout
        self.cameras_drawn = []
        self.num_msgs_to_start = config.num_msgs_to_start

        # Init ROS
        rclpy.init(args=None)

    def setup(self, test_mode: Literal["test", "val", "inference"] = "val") -> None:
        """Setup the Trainer by calling other setup functions.

        Args:
            test_mode:
                'val': loads train/val datasets into memory
                'test': loads train/test datasets into memory
                'inference': does not load any dataset into memory
        """
        self.pipeline = self.config.pipeline.setup(
            device=self.device,
            test_mode=test_mode,
            world_size=self.world_size,
            local_rank=self.local_rank,
            grad_scaler=self.grad_scaler,
        )
        self.optimizers = self.setup_optimizers()

        # set up viewer if enabled
        viewer_log_path = self.base_dir / self.config.viewer.relative_log_filename
        self.viewer_state, banner_messages = None, None
        if self.config.is_viewer_legacy_enabled() and self.local_rank == 0:
            CONSOLE.print(
                "[bold red] (NerfBridge) Legacy Viewer is not supported by NerfBridge!"
            )
        if self.config.is_viewer_enabled() and self.local_rank == 0:
            datapath = self.config.data
            if datapath is None:
                datapath = self.base_dir
            self.viewer_state = ROSViewer(
                self.config.viewer,
                log_filename=viewer_log_path,
                datapath=datapath,
                pipeline=self.pipeline,
                trainer=self,
                train_lock=self.train_lock,
                share=self.config.viewer.make_share_url,
            )
            banner_messages = self.viewer_state.viewer_info

        self._check_viewer_warnings()

        self._load_checkpoint()

        self.callbacks = self.pipeline.get_training_callbacks(
            TrainingCallbackAttributes(
                optimizers=self.optimizers,
                grad_scaler=self.grad_scaler,
                pipeline=self.pipeline,
                trainer=self,
            )
        )

        # set up writers/profilers if enabled
        writer_log_path = self.base_dir / self.config.logging.relative_log_dir
        writer.setup_event_writer(
            self.config.is_wandb_enabled(),
            self.config.is_tensorboard_enabled(),
            self.config.is_comet_enabled(),
            log_dir=writer_log_path,
            experiment_name=self.config.experiment_name,
            project_name=self.config.project_name,
        )
        writer.setup_local_writer(
            self.config.logging,
            max_iter=self.config.max_num_iterations,
            banner_messages=banner_messages,
        )
        writer.put_config(
            name="config", config_dict=dataclasses.asdict(self.config), step=0
        )
        profiler.setup_profiler(self.config.logging, writer_log_path)

        if self.config.enable_cbf:
            self.setup_cbf_node()

        if self.config.show_robot_cbf_in_viewer and self.config.is_viewer_enabled():
            self.viewer_state.setup_robot_viewer_node()
            self.pipeline.datamanager.train_image_dataloader.executor.add_node(
                self.viewer_state.node
            )

        # # Start a thread for processing all of the ros callbacks
        self.pipeline.datamanager.train_image_dataloader.start_ros_thread()

        # Start Status check loop
        start = time.perf_counter()
        status = False
        CONSOLE.print(
            f"[bold green] (NerfBridge) Waiting to recieve {self.num_msgs_to_start} images..."
        )
        # with CONSOLE.status("", spinner="dots") as status:
        while time.perf_counter() - start < self.msg_timeout:
            dl_idx = self.pipeline.datamanager.train_image_dataloader.current_idx
            if dl_idx >= (self.num_msgs_to_start - 1):
                status = True
                break
            else:
                status_str = f"[green] (NerfBridge) Images received: {dl_idx}"
                # status.update(status_str)
            time.sleep(0.05)

        self.dataset = self.pipeline.datamanager.train_dataset  # pyright: ignore

        if not status:
            raise NameError(
                "(NerfBridge) ROSTrainer setup() timed out, check that messages \
                are being published and that config.json correctly specifies topic names."
            )
        else:
            CONSOLE.print(
                "[bold green] (NerfBridge) Pre-train image buffer filled, starting training!"
            )

    def setup_cbf_node(self):
        self.cbf_node = rclpy.create_node("nerfbridge_cbf")
        self.cbf_publisher = self.cbf_node.create_publisher(
            Float32MultiArray, "/cbf_optimal", 3
        )

        self.cbf_subscriber = self.cbf_node.create_subscription(
            Float32MultiArray, "/cbf_desired", self.cbf_callback, 3
        )

        self.barrier_pub = self.cbf_node.create_publisher(
            Float32MultiArray, "/barrier_data", 3
        )
        self.pipeline.datamanager.train_image_dataloader.executor.add_node(
            self.cbf_node
        )

    def cbf_callback(self, msg):
        # print("Received CBF message")

        start_time = time.time()

        # u_des = torch.tensor(msg.data).to(self.device)
        # u_des = torch.zeros(3).to(self.device)
        u_des = torch.tensor([msg.data[0], msg.data[1], msg.data[2]])

        # state = torch.zeros(6).to(self.device)
        state = torch.tensor(
            [
                msg.data[6],
                msg.data[7],
                msg.data[8],
                msg.data[3],
                msg.data[4],
                msg.data[5],
            ]
        ).to(self.device)
        #
        # viewer_state = [msg.data[6], msg.data[7], msg.data[8], msg.data[9]]
        # self.pipeline.model.viewer_drone_state = viewer_state
        # self.viewer_state.update_robot()

        now = time.time()
        u_opt, h_min = self.pipeline.model.cbf(u_des, state)
        cbf_time = time.time() - now

        if u_opt is None:
            u_opt = u_des
            h_min = torch.tensor([torch.nan])

        safe = h_min > 0.0
        done = "DONE" if self.pipeline.datamanager.done_images else ""
        if safe:
            CONSOLE.print(
                f"[green] h_min = {h_min.item(): 0.4f}, dt = {cbf_time:0.4f} {done}"
            )
        else:
            CONSOLE.print(
                f"[bold red] h_min = {h_min.item(): 0.4f}, dt = {cbf_time:0.4f} {done}"
            )

        # print(f'current state {state}')
        # print(f'udes {u_des} uopt {u_opt}')
        # print(f'sending {u_opt.cpu().numpy()}')
        # now publish the optimal control
        u_opt_msg = Float32MultiArray()
        # make sure dtype is float32
        # print(u_opt)
        data = u_opt.tolist()
        # print(data)
        u_opt_msg.data = data
        # time.sleep(0.1)
        self.cbf_publisher.publish(u_opt_msg)

        barrier_msg = Float32MultiArray()
        barrier_msg.data = [h_min.item(), float(cbf_time)]
        self.barrier_pub.publish(barrier_msg)

        # print(f'total time elapse {time.time() - start_time:.4f}')

    # def render_paper_image_cb(self, step):
    #     """Callback for rendering paper image."""
    #     if not step == 15000:
    #         return
    #     trial = 3
    #     if trial == 3:
    #         idx = 3
    #     elif trial == 5:
    #         idx = 0
    #     elif trial == 2:
    #         idx = 111
    #     else:
    #         idx = 0
    #     save_dir = (
    #         Path(__file__).parent.parent.parent / f"trial{trial}" / "paper_images"
    #     )
    #     save_dir.mkdir(parents=True, exist_ok=True)
    #     with torch.no_grad():
    #         self.pipeline.model.render_paper = True
    #         camera = self.pipeline.datamanager.train_dataset.cameras[idx : idx + 1].to(
    #             self.device
    #         )
    #         camera.metadata = {"cam_idx": idx}
    #         image_data = self.pipeline.datamanager.train_dataset[idx]
    #         outputs = self.pipeline.model.get_outputs_for_camera(camera)
    #         rgb = outputs["rgb"]
    #         depth = outputs["depth"]
    #         image_render = rgb[..., :3].cpu().numpy() * 255
    #         image_render = cv2.cvtColor(image_render, cv2.COLOR_RGB2BGR)
    #         image_gt = image_data["image"].cpu().numpy() * 255
    #         image_gt = cv2.cvtColor(image_gt, cv2.COLOR_RGB2BGR)
    #         depth_render = depth.cpu().numpy()
    #         depth_render = (depth_render - depth_render.min()) / (
    #             depth_render.max() - depth_render.min()
    #         )
    #         depth_render = (depth_render * 255).astype(np.uint8)
    #         depth_render = cv2.applyColorMap(depth_render, cv2.COLORMAP_JET)
    #
    #         fx, fy = camera.fx[0].item(), camera.fy[0].item()
    #         cx, cy = camera.cx[0].item(), camera.cy[0].item()
    #         H = camera.image_height[0].item()
    #         W = camera.image_width[0].item()
    #         K = np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])
    #
    #         pc_data = self.pipeline.datamanager.train_dataset.pc_tensor[idx]
    #         pc_data = pc_data[~torch.all(pc_data == 0, axis=1)]
    #         proj, _ = cv2.projectPoints(
    #             pc_data.numpy(), np.zeros(3), np.zeros(3), K, np.zeros(5)
    #         )
    #         proj = torch.from_numpy(proj.squeeze())
    #         umask = (0 <= proj[:, 0]) & (proj[:, 0] < W)
    #         vmask = (0 <= proj[:, 1]) & (proj[:, 1] < H)
    #         in_view = umask & vmask
    #         pc_data = pc_data[in_view]
    #         proj = proj[in_view]
    #         proj = proj.long()
    #         depth_gt = torch.zeros((H, W))
    #         depth_gt[proj[:, 1], proj[:, 0]] = pc_data[:, 2]
    #         depth_gt = depth_gt.numpy()
    #         depth_gt = (depth_gt - depth_gt.min()) / (depth_gt.max() - depth_gt.min())
    #         depth_gt = (depth_gt * 255).astype(np.uint8)
    #         # Inflate the depth_gt pixels
    #         depth_gt = cv2.dilate(depth_gt, np.ones((4, 4), np.uint8))
    #         depth_gt = cv2.applyColorMap(depth_gt, cv2.COLORMAP_JET)
    #
    #         cv2.imwrite(str(save_dir / f"image_render.png"), image_render)
    #         cv2.imwrite(str(save_dir / f"image_gt.png"), image_gt)
    #         cv2.imwrite(str(save_dir / f"depth_render.png"), depth_render)
    #         cv2.imwrite(str(save_dir / f"depth_gt.png"), depth_gt)
    #     breakpoint()
