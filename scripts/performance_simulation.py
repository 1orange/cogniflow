#!/usr/bin/env python3
"""
Performance Simulation: Comparing Rust-Decoupled vs Coupled BCI Approaches

This script simulates the performance characteristics of two BCI data acquisition approaches:

1. Rust-Decoupled: Rust driver runs in separate thread, decoupled from Python game loop
2. Coupled: BCI processing done directly in main game loop (blocking approach)

The simulation measures:
- Frame rate stability and drops
- BCI processing latency
- Data stream continuity
- System responsiveness under load

Usage:
    python scripts/performance_simulation.py --duration 60 --stress-level 0.5
"""

import time
import threading
import numpy as np
import argparse
import matplotlib.pyplot as plt
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Optional
import statistics
import concurrent.futures


@dataclass
class PerformanceMetrics:
    """Performance metrics collected during simulation."""
    frame_times: List[float]
    bci_latencies: List[float]
    data_drops: int
    total_frames: int
    total_bci_predictions: int
    stress_events: int

    @property
    def avg_frame_time(self) -> float:
        return statistics.mean(self.frame_times) if self.frame_times else 0

    @property
    def frame_rate_stability(self) -> float:
        """Coefficient of variation of frame times (lower is more stable)."""
        if len(self.frame_times) < 2:
            return 0
        return statistics.stdev(self.frame_times) / statistics.mean(self.frame_times)

    @property
    def avg_bci_latency(self) -> float:
        return statistics.mean(self.bci_latencies) if self.bci_latencies else 0

    @property
    def data_drop_rate(self) -> float:
        """Percentage of frames where data was dropped."""
        return (self.data_drops / self.total_frames) * 100 if self.total_frames > 0 else 0


class MockRustDataProvider:
    """
    Simulates the current Rust-decoupled approach.
    - Rust driver runs continuously in background
    - Python polls non-blockingly
    - Buffer prevents data loss
    """

    def __init__(self, sample_rate: int = 128, channels: int = 14, buffer_size_seconds: int = 10):
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = sample_rate * buffer_size_seconds
        self.buffer = deque(maxlen=self.buffer_size)
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.sample_counter = 0

    def start(self):
        """Start the simulated Rust driver thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._rust_driver_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the driver."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _rust_driver_loop(self):
        """Simulates continuous Rust data acquisition at precise intervals."""
        interval = 1.0 / self.sample_rate
        last_time = time.time()

        while self.running:
            current_time = time.time()
            # Precise timing simulation
            if current_time - last_time >= interval:
                # Generate sample (simulating real EEG data)
                sample = self._generate_sample()
                with self.lock:
                    self.buffer.append(sample)
                last_time = current_time
            else:
                time.sleep(0.0001)  # Minimal sleep to prevent busy waiting

    def _generate_sample(self) -> np.ndarray:
        """Generate synthetic EEG-like sample."""
        self.sample_counter += 1
        t = self.sample_counter / self.sample_rate

        # Simulate realistic EEG: mix of alpha, beta, theta waves + noise
        alpha = 20 * np.sin(2 * np.pi * 10 * t)
        beta = 10 * np.sin(2 * np.pi * 20 * t)
        theta = 15 * np.sin(2 * np.pi * 6 * t)
        noise = 5 * np.random.randn()

        value = alpha + beta + theta + noise
        return np.full(self.channels, value)

    def read(self, n_samples: int) -> np.ndarray:
        """Non-blocking read from buffer (like current DataProvider)."""
        with self.lock:
            available = len(self.buffer)
            n_read = min(n_samples, available)

            if n_read == 0:
                return np.zeros((0, self.channels))

            samples = []
            for _ in range(n_read):
                samples.append(self.buffer.popleft())

            return np.array(samples)


class MockCoupledDataProvider:
    """
    Simulates a coupled approach where BCI processing blocks the game loop.
    - No background thread
    - Data acquisition happens during game loop
    - Potential for blocking delays
    """

    def __init__(self, sample_rate: int = 128, channels: int = 14):
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_counter = 0

    def start(self):
        """No-op for coupled approach."""
        pass

    def stop(self):
        """No-op for coupled approach."""
        pass

    def read(self, n_samples: int) -> np.ndarray:
        """Blocking read that simulates processing delays."""
        # Simulate processing delay (what might happen with pure Python approach)
        processing_delay = np.random.exponential(0.002)  # Mean 2ms delay
        time.sleep(processing_delay)

        samples = []
        for _ in range(n_samples):
            self.sample_counter += 1
            t = self.sample_counter / self.sample_rate
            # Same signal generation as decoupled
            alpha = 20 * np.sin(2 * np.pi * 10 * t)
            beta = 10 * np.sin(2 * np.pi * 20 * t)
            theta = 15 * np.sin(2 * np.pi * 6 * t)
            noise = 5 * np.random.randn()
            value = alpha + beta + theta + noise
            samples.append(np.full(self.channels, value))

        return np.array(samples)


class MockBCIModel:
    """Mock BCI model that simulates processing time."""

    def __init__(self, processing_time_ms: float = 50):
        self.processing_time_ms = processing_time_ms

    def predict(self, data: np.ndarray) -> str:
        """Simulate BCI prediction with realistic processing time."""
        time.sleep(self.processing_time_ms / 1000.0)
        # Simple mock prediction based on signal amplitude
        mean_signal = np.mean(data)
        if mean_signal > 5:
            return "forward"
        elif mean_signal < -5:
            return "backward"
        else:
            return "rest"


class GameLoopSimulator:
    """Simulates a game loop with BCI control."""

    def __init__(self, data_provider, bci_model=None, target_fps: int = 60):
        self.data_provider = data_provider
        self.bci_model = bci_model
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps

        # BCI processing state (similar to driving scene)
        self.sample_rate = 128
        self.window_size = int(2.0 * self.sample_rate)  # 2 second window
        self.hop_size = int(0.5 * self.sample_rate)     # 0.5 second hop
        self.channel_buffer = np.zeros((0, 14))
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.pending_result = None
        self.processing = False

    def simulate_frame(self, stress_factor: float = 0) -> tuple[float, bool, Optional[float]]:
        """
        Simulate one frame of the game loop.

        Returns:
            (frame_time, data_available, bci_latency)
        """
        frame_start = time.time()

        # Simulate game loop work
        self._simulate_game_work(stress_factor)

        # Handle BCI processing
        bci_latency = None
        data_available = True

        if self.bci_model:
            # Read new data
            dt = self.frame_interval
            n_samples = int(dt * self.sample_rate)
            if n_samples > 0:
                samples = self.data_provider.read(n_samples)
                if samples.shape[0] > 0:
                    self.channel_buffer = np.vstack([self.channel_buffer, samples])
                    # Keep buffer from growing too large
                    if self.channel_buffer.shape[0] > self.window_size * 3:
                        self.channel_buffer = self.channel_buffer[-self.window_size * 2:, :]
                else:
                    data_available = False

            # Check for completed async BCI result
            if self.pending_result and self.pending_result.done():
                try:
                    result = self.pending_result.result()
                    bci_latency = time.time() - frame_start
                    self.pending_result = None
                    self.processing = False
                except Exception:
                    self.pending_result = None
                    self.processing = False

            # Start new BCI processing if we have enough data and not already processing
            if (self.channel_buffer.shape[0] >= self.window_size and
                not self.processing):
                window = self.channel_buffer[:self.window_size, :]
                self.channel_buffer = self.channel_buffer[self.hop_size:, :]
                self.pending_result = self.executor.submit(self._process_bci, window)
                self.processing = True

        frame_time = time.time() - frame_start
        return frame_time, data_available, bci_latency

    def _simulate_game_work(self, stress_factor: float):
        """Simulate game loop work with optional stress."""
        base_work_time = 0.005  # 5ms base work
        stress_time = stress_factor * 0.02  # Up to 20ms additional stress
        time.sleep(base_work_time + stress_time)

    def _process_bci(self, data: np.ndarray) -> str:
        """Async BCI processing."""
        return self.bci_model.predict(data)


def run_simulation(
    approach: str,
    duration_seconds: int,
    stress_level: float,
    stress_events: int = 0
) -> PerformanceMetrics:
    """
    Run performance simulation for one approach.

    Args:
        approach: "rust_decoupled" or "coupled"
        duration_seconds: How long to run simulation
        stress_level: Base stress factor (0-1)
        stress_events: Number of high-stress events to inject
    """
    print(f"Running {approach} simulation for {duration_seconds}s with stress level {stress_level}")

    # Setup data provider
    if approach == "rust_decoupled":
        provider = MockRustDataProvider()
        bci_model = MockBCIModel(processing_time_ms=50)  # Realistic ML inference time
    else:  # coupled
        provider = MockCoupledDataProvider()
        bci_model = MockBCIModel(processing_time_ms=50)

    provider.start()

    # Setup game loop simulator
    simulator = GameLoopSimulator(provider, bci_model, target_fps=60)

    # Run simulation
    start_time = time.time()
    end_time = start_time + duration_seconds

    frame_times = []
    bci_latencies = []
    data_drops = 0
    total_frames = 0
    bci_predictions = 0

    stress_event_times = []
    if stress_events > 0:
        # Schedule stress events randomly throughout simulation
        stress_event_times = [
            start_time + np.random.uniform(0, duration_seconds)
            for _ in range(stress_events)
        ]

    try:
        while time.time() < end_time:
            frame_start = time.time()

            # Check for stress events
            current_stress = stress_level
            for stress_time in stress_event_times:
                if abs(time.time() - stress_time) < 0.1:  # 100ms stress window
                    current_stress = min(1.0, stress_level + 0.5)  # Extra stress
                    break

            # Simulate frame
            frame_time, data_available, bci_latency = simulator.simulate_frame(current_stress)

            frame_times.append(frame_time)
            total_frames += 1

            if not data_available:
                data_drops += 1

            if bci_latency is not None:
                bci_latencies.append(bci_latency)
                bci_predictions += 1

            # Maintain target frame rate
            elapsed = time.time() - frame_start
            sleep_time = max(0, simulator.frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        provider.stop()
        simulator.executor.shutdown(wait=True)

    return PerformanceMetrics(
        frame_times=frame_times,
        bci_latencies=bci_latencies,
        data_drops=data_drops,
        total_frames=total_frames,
        total_bci_predictions=bci_predictions,
        stress_events=len(stress_event_times)
    )


def plot_comparison_results(rust_metrics: PerformanceMetrics, coupled_metrics: PerformanceMetrics):
    """Create comparison plots."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Frame time distributions
    axes[0, 0].hist(rust_metrics.frame_times, alpha=0.7, label='Rust-Decoupled', bins=50)
    axes[0, 0].hist(coupled_metrics.frame_times, alpha=0.7, label='Coupled', bins=50)
    axes[0, 0].set_xlabel('Frame Time (s)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Frame Time Distribution')
    axes[0, 0].legend()
    axes[0, 0].axvline(1/60, color='red', linestyle='--', alpha=0.7, label='60 FPS target')

    # BCI latency comparison
    if rust_metrics.bci_latencies and coupled_metrics.bci_latencies:
        axes[0, 1].boxplot([rust_metrics.bci_latencies, coupled_metrics.bci_latencies],
                          labels=['Rust-Decoupled', 'Coupled'])
        axes[0, 1].set_ylabel('Latency (s)')
        axes[0, 1].set_title('BCI Processing Latency')

    # Frame rate stability over time (rolling average)
    window_size = 60  # 1 second at 60 FPS
    rust_rolling = [statistics.mean(rust_metrics.frame_times[i:i+window_size])
                   for i in range(0, len(rust_metrics.frame_times)-window_size, window_size)]
    coupled_rolling = [statistics.mean(coupled_metrics.frame_times[i:i+window_size])
                      for i in range(0, len(coupled_metrics.frame_times)-window_size, window_size)]

    axes[1, 0].plot(rust_rolling, label='Rust-Decoupled')
    axes[1, 0].plot(coupled_rolling, label='Coupled')
    axes[1, 0].set_xlabel('Time Window')
    axes[1, 0].set_ylabel('Avg Frame Time (s)')
    axes[1, 0].set_title('Frame Rate Stability Over Time')
    axes[1, 0].legend()

    # Performance summary
    labels = ['Avg Frame Time', 'Frame Stability\n(CV)', 'Data Drop Rate', 'BCI Latency']
    rust_values = [
        rust_metrics.avg_frame_time * 1000,  # Convert to ms
        rust_metrics.frame_rate_stability,
        rust_metrics.data_drop_rate,
        rust_metrics.avg_bci_latency * 1000
    ]
    coupled_values = [
        coupled_metrics.avg_frame_time * 1000,
        coupled_metrics.frame_rate_stability,
        coupled_metrics.data_drop_rate,
        coupled_metrics.avg_bci_latency * 1000
    ]

    x = np.arange(len(labels))
    width = 0.35

    axes[1, 1].bar(x - width/2, rust_values, width, label='Rust-Decoupled', alpha=0.7)
    axes[1, 1].bar(x + width/2, coupled_values, width, label='Coupled', alpha=0.7)
    axes[1, 1].set_ylabel('Value')
    axes[1, 1].set_title('Performance Summary')
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(labels, rotation=45)
    axes[1, 1].legend()

    plt.tight_layout()
    plt.savefig('performance_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='BCI Performance Simulation')
    parser.add_argument('--duration', type=int, default=30,
                       help='Simulation duration in seconds')
    parser.add_argument('--stress-level', type=float, default=0.0,
                       help='Base stress level (0.0-1.0)')
    parser.add_argument('--stress-events', type=int, default=0,
                       help='Number of high-stress events to inject')
    parser.add_argument('--runs', type=int, default=1,
                       help='Number of simulation runs for averaging')
    parser.add_argument('--plot', action='store_true',
                       help='Generate comparison plots')

    args = parser.parse_args()

    print("🚀 Starting BCI Performance Simulation")
    print(f"Duration: {args.duration}s | Stress Level: {args.stress_level} | Runs: {args.runs}")
    print("=" * 60)

    # Run simulations
    rust_results = []
    coupled_results = []

    for run in range(args.runs):
        print(f"\nRun {run + 1}/{args.runs}")

        # Rust-decoupled simulation
        rust_metrics = run_simulation(
            "rust_decoupled", args.duration, args.stress_level, args.stress_events
        )
        rust_results.append(rust_metrics)

        # Coupled simulation
        coupled_metrics = run_simulation(
            "coupled", args.duration, args.stress_level, args.stress_events
        )
        coupled_results.append(coupled_metrics)

    # Average results across runs
    def average_metrics(results: List[PerformanceMetrics]) -> PerformanceMetrics:
        return PerformanceMetrics(
            frame_times=[t for r in results for t in r.frame_times],
            bci_latencies=[l for r in results for l in r.bci_latencies],
            data_drops=sum(r.data_drops for r in results) // len(results),
            total_frames=sum(r.total_frames for r in results) // len(results),
            total_bci_predictions=sum(r.total_bci_predictions for r in results) // len(results),
            stress_events=results[0].stress_events
        )

    avg_rust = average_metrics(rust_results)
    avg_coupled = average_metrics(coupled_results)

    # Print results
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE RESULTS")
    print("=" * 60)

    print(f"\n🎯 RUST-DECOUPLED APPROACH:")
    print(f"  Average Frame Time: {avg_rust.avg_frame_time*1000:.2f}ms")
    print(f"  Frame Rate Stability (CV): {avg_rust.frame_rate_stability:.4f}")
    print(f"  Data Drop Rate: {avg_rust.data_drop_rate:.2f}%")
    print(f"  Total BCI Predictions: {avg_rust.total_bci_predictions}")
    print(f"  Average BCI Latency: {avg_rust.avg_bci_latency*1000:.2f}ms")

    print(f"\n🔗 COUPLED APPROACH:")
    print(f"  Average Frame Time: {avg_coupled.avg_frame_time*1000:.2f}ms")
    print(f"  Frame Rate Stability (CV): {avg_coupled.frame_rate_stability:.4f}")
    print(f"  Data Drop Rate: {avg_coupled.data_drop_rate:.2f}%")
    print(f"  Total BCI Predictions: {avg_coupled.total_bci_predictions}")
    print(f"  Average BCI Latency: {avg_coupled.avg_bci_latency*1000:.2f}ms")

    # Performance comparison
    print(f"\n⚡ COMPARISON:")
    frame_time_improvement = ((avg_coupled.avg_frame_time - avg_rust.avg_frame_time) / avg_coupled.avg_frame_time) * 100
    stability_improvement = ((avg_coupled.frame_rate_stability - avg_rust.frame_rate_stability) / avg_coupled.frame_rate_stability) * 100
    drop_rate_improvement = avg_coupled.data_drop_rate - avg_rust.data_drop_rate
    latency_improvement = ((avg_coupled.avg_bci_latency - avg_rust.avg_bci_latency) / avg_coupled.avg_bci_latency) * 100

    print(f"  Frame Time Improvement: {frame_time_improvement:.1f}%")
    print(f"  Stability Improvement: {stability_improvement:.1f}%")
    print(f"  Data Drop Rate Reduction: {drop_rate_improvement:.1f}%")
    print(f"  BCI Latency Improvement: {latency_improvement:.1f}%")
    if args.plot:
        print("\n📈 Generating comparison plots...")
        plot_comparison_results(avg_rust, avg_coupled)
        print("Plot saved as 'performance_comparison.png'")

    print("\n✅ Simulation complete!")


if __name__ == "__main__":
    main()
