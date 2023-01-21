import sys
import os
import logging
import numpy as np
from typing import Tuple
from src.MovementType import MovementType

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
sys.path.insert(0, __location__)


class Evolver:
    """Evolver to implement custom video with patch applied.

    Attributes:
        frame_w(int)
        frame_h(int)
        origin(ndarray)
        patch(np.ndarray)
        fps(int)
    """

    def __init__(self, frame_w: int, frame_h: int, origin_w: int, origin_h: int, patch: np.ndarray, fps: int) -> None:
        # input
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.origin = np.array([origin_h, origin_w], dtype=float)
        self.patch = patch
        self.fps = fps

        # internal states
        self.v = 0
        self.step = float(1 / self.fps)

        # output
        self.frames = []
        self.gth = []

    def update_origin(self, origin_w: int, origin_h: int) -> None:
        self.origin = np.array([origin_h, origin_w], dtype=float)

    def compute_evolutions(self, route: list) -> Tuple[list, list]:
        """ Compute evolutions for each steps in route list.

            Args:
                route(list): list of steps for patch applied

            Returns:
                frames(list): list of frames to animate the path
                gth(list): list of path center coord in the frame
        """
        for (d_w, d_h, command, time_ms) in route:
            # compute dest and final time [s]
            dest = np.array([d_h, d_w], dtype=float)
            t_f = time_ms / 1000

            # compute velocity
            num_frames = int(self.fps * t_f)
            self.v = (dest - self.origin) / t_f
            if command.value == MovementType.urm.value:
                self._compute_linear(num_frames)
            elif command.value == MovementType.uarm.value:
                a = (dest - self.origin) / (t_f ** 2)
                self._compute_acc(num_frames, a)
            elif command.value == MovementType.trap.value:
                # TODO
                pass
            else:
                logging.error("Wrong type!")
                pass

            # update origin for next command
            self.origin = dest
        return self.frames, self.gth

    def _compute_linear(self, num_frames: int) -> None:
        """Compute frames with uniformly rectilinear motion (URM) for patch.

        This method updates frames and gth attributes.

        Args:
            num_frames(int): number of desired frames
        """
        for i in range(num_frames + 1):
            # motion law
            t = i * self.step
            x = self.origin + self.v * t

            # save frame
            frame = np.zeros((self.frame_h, self.frame_w, 3))
            frame = self.apply_patch(frame, self.patch, x)
            self.frames.append(frame)
            self.gth.append(x)

    def _compute_acc(self, num_frames: int, a: float) -> None:
        """Compute frames with (UARM) motion law.

        This method updates frames and gth attributes.

        Args:
            num_frames(int): number of desired frames
            a(float): acceleration
        """
        for i in range(num_frames + 1):
            # motion law
            t = i * self.step
            x = self.origin + a * (t ** 2)

            # save frame
            frame = np.zeros((self.frame_h, self.frame_w, 3))
            frame = self.apply_patch(frame, self.patch, x)
            self.frames.append(frame)
            self.gth.append(x)

    @staticmethod
    def apply_patch(frame: np.ndarray, patch: np.ndarray, x: np.ndarray) -> np.ndarray:
        """To Apply patch in desired frame.

        Args:
            frame(ndarray)
            patch(ndarray)
            x(ndarray): center of patch in frame reference

        Return:
            frame with apllied patch
        """
        # compute coord
        x = np.floor(x)
        r_i = int(x[0] - int(patch.shape[0] / 2))
        r_f = int(x[0] + int(patch.shape[0] / 2) + 1)
        c_i = int(x[1] - int(patch.shape[1] / 2))
        c_f = int(x[1] + int(patch.shape[1] / 2) + 1)

        # out of border
        if r_i >= frame.shape[0] or r_f <= 0 or c_i >= frame.shape[1] or c_f <= 0:
            return frame

        # fix frame indices to handle edges
        fr_i = max(0, r_i)
        fr_f = min(frame.shape[0], r_f)
        fc_i = max(0, c_i)
        fc_f = min(frame.shape[1], c_f)

        # fix path indices to handle edges
        pc_f = patch.shape[1] - (c_f - fc_f)
        pc_i = fc_i - c_i
        pr_f = patch.shape[0] - (r_f - fr_f)
        pr_i = fr_i - r_i

        # patch
        frame = frame.copy()
        frame[fr_i:fr_f, fc_i:fc_f, :] = patch[pr_i:pr_f, pc_i:pc_f, :]
        return frame
