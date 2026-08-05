from __future__ import annotations

import math
from dataclasses import dataclass, field
from time import monotonic
from typing import Tuple, Optional


@dataclass(slots=True)
class IMU:
    """Simple IMU sensor model with state and helpers.

    Attributes:
        accel: Accelerometer reading (ax, ay, az) in m/s^2.
        gyro: Gyroscope reading (gx, gy, gz) in °/s.
        mag: Magnetometer reading (mx, my, mz) in µT (optional).
        temp: Temperature in degrees Celsius (optional).
        gyro_bias: Per-axis gyro bias (gx, gy, gz) applied on update.
        sample_rate: Expected sensor sample rate in Hz (used when dt omitted).
        alpha: Complementary filter blending factor (0..1).
        roll, pitch, yaw: Current attitude estimate in degrees.
    """

    accel: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    mag: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    temp: Optional[float] = None

    gyro_bias: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    sample_rate: float = 100.0
    alpha: float = 0.98

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    _last_time: float = field(default_factory=monotonic, init=False)

    def set_biases(self, gyro_bias: Tuple[float, float, float]) -> None:
        self.gyro_bias = gyro_bias

    def calibrate_gyro(self, samples: list[Tuple[float, float, float]]) -> None:
        if not samples:
            return
        gx = sum(s[0] for s in samples) / len(samples)
        gy = sum(s[1] for s in samples) / len(samples)
        gz = sum(s[2] for s in samples) / len(samples)
        self.gyro_bias = (gx, gy, gz)

    def update(
        self,
        accel: Tuple[float, float, float],
        gyro: Tuple[float, float, float],
        mag: Optional[Tuple[float, float, float]] = None,
        dt: Optional[float] = None,
    ) -> None:
        now = monotonic()
        if dt is None:
            dt = 1.0 / self.sample_rate if self.sample_rate > 0 else now - self._last_time
        if dt <= 0:
            dt = max(1e-6, now - self._last_time)

        self._last_time = now
        self.accel = accel
        self.gyro = gyro
        if mag is not None:
            self.mag = mag

        gx = gyro[0] - self.gyro_bias[0]
        gy = gyro[1] - self.gyro_bias[1]
        gz = gyro[2] - self.gyro_bias[2]

        # Integrate gyro (degrees)
        self.roll += gx * dt
        self.pitch += gy * dt
        self.yaw += gz * dt

        ax, ay, az = accel
        if ax == 0 and ay == 0 and az == 0:
            return

        # Compute accel-based angles (radians → degrees)
        roll_acc = math.degrees(math.atan2(ay, az))
        pitch_acc = math.degrees(math.atan2(-ax, math.hypot(ay, az)))

        self.roll = self.alpha * self.roll + (1.0 - self.alpha) * roll_acc
        self.pitch = self.alpha * self.pitch + (1.0 - self.alpha) * pitch_acc

        # Normalize yaw to [0, 360)
        self.yaw = (self.yaw + 360.0) % 360.0

    def get_attitude(self) -> Tuple[float, float, float]:
        return self.roll, self.pitch, self.yaw

    def accel_magnitude(self) -> float:
        ax, ay, az = self.accel
        return math.sqrt(ax * ax + ay * ay + az * az)

    def reset(self) -> None:
        self.accel = (0.0, 0.0, 0.0)
        self.gyro = (0.0, 0.0, 0.0)
        self.mag = (0.0, 0.0, 0.0)
        self.temp = None
        self.roll = self.pitch = self.yaw = 0.0
        self._last_time = monotonic()

    def to_dict(self) -> dict:
        return {
            "accel": self.accel,
            "gyro": self.gyro,
            "mag": self.mag,
            "temp": self.temp,
            "gyro_bias": self.gyro_bias,
            "sample_rate": self.sample_rate,
            "alpha": self.alpha,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
        }
