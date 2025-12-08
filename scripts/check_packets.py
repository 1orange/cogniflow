#!/usr/bin/env python3
"""
Simple script to check if Emotiv packets are flowing.

This script provides a real-time monitor showing packet flow and basic device stats.
Press Ctrl+C to stop.
"""

import sys
import time


def clear_line():
    """Clear the current terminal line."""
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def print_status(message, end="\r"):
    """Print status message."""
    clear_line()
    sys.stdout.write(message)
    sys.stdout.flush()


def main():
    """Monitor packet flow from Emotiv device."""
    try:
        import emotiv_rs
    except ImportError:
        print("❌ Error: emotiv_rs module not installed")
        print("\nTo install, run:")
        print("  cd bci/emotiv/lib")
        print("  poetry run maturin develop --release")
        return 1

    print("=" * 70)
    print(" 📡 EMOTIV PACKET FLOW MONITOR")
    print("=" * 70)
    print("\nNote: This monitor reads the LATEST packet each time,")
    print("discarding old queued packets to show real-time data.")
    print("'Packet loss' shows how many packets were skipped (expected behavior).")
    print("\nAttempting to connect to Emotiv device...")

    # Create reader
    reader = emotiv_rs.EmotivReader(None, None, None, None)
    reader.start()

    # Give it time to connect
    time.sleep(0.5)

    if not reader.is_running():
        print("❌ Failed to connect to device")
        print("\nPossible reasons:")
        print("  • Device is not plugged in")
        print("  • Device is not powered on")
        print("  • USB permissions issue (try running with sudo)")
        print("  • Device is already in use by another application")
        return 1

    print("✅ Successfully connected!\n")
    print("-" * 70)
    print("Monitoring packet flow... (Press Ctrl+C to stop)")
    print("-" * 70)
    print()

    # Monitoring loop
    packets_received = 0
    start_time = time.time()
    last_update = start_time
    last_counter = None
    packet_losses = 0
    last_battery = None
    last_quality = None
    first_packet_seen = False

    try:
        while True:
            parsed = reader.poll_parsed()

            if parsed:
                packets_received += 1
                current_time = time.time()

                # Check for packet loss (skip the first transition to establish baseline)
                if last_counter is not None:
                    expected = (last_counter + 1) % 256
                    # Only count loss after we've seen at least one valid transition
                    if parsed["counter"] != expected and first_packet_seen:
                        gap = (parsed["counter"] - expected) % 256
                        packet_losses += (
                            gap  # Actually "packets skipped" for latest-data mode
                        )
                    # Mark that we've now established a baseline
                    first_packet_seen = True

                last_counter = parsed["counter"]

                # Update battery and quality
                last_battery = parsed["battery"]
                last_quality = parsed["quality"]

                # Update display every 0.1 seconds
                if current_time - last_update >= 0.1:
                    elapsed = current_time - start_time
                    rate = packets_received / elapsed if elapsed > 0 else 0

                    # Build status line
                    status = "🟢 PACKETS FLOWING  "
                    status += f"│ Count: {packets_received:6d}  "
                    status += f"│ Rate: {rate:6.1f} Hz  "
                    status += f"│ Battery: {last_battery:3d}%  "

                    # Show quality indicator (average of all sensors)
                    if last_quality:
                        avg_quality = sum(last_quality.values()) / len(last_quality)
                        quality_emoji = ["⚫", "🔴", "🟠", "🟡", "🟢"]
                        quality_idx = min(int(avg_quality), 4)
                        status += f"│ Signal: {quality_emoji[quality_idx]}  "

                    if packet_losses > 0:
                        skip_rate = (
                            packet_losses / (packets_received + packet_losses)
                        ) * 100
                        status += f"│ Skipped: {packet_losses} ({skip_rate:.1f}%)"

                    print_status(status)
                    last_update = current_time
            else:
                # No packet available
                time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n\n" + "-" * 70)
        print("📊 SESSION SUMMARY")
        print("-" * 70)

        elapsed = time.time() - start_time
        avg_rate = packets_received / elapsed if elapsed > 0 else 0

        print(f"Duration:        {elapsed:.1f} seconds")
        print(f"Packets read:    {packets_received}")
        print(f"Average rate:    {avg_rate:.1f} Hz")
        print(f"Packets skipped: {packet_losses}")

        if packet_losses > 0:
            total_packets = packets_received + packet_losses
            skip_rate = (packet_losses / total_packets) * 100
            print(f"Skip rate:       {skip_rate:.2f}% (normal for real-time mode)")

        if last_battery is not None:
            print(f"Final battery:   {last_battery}%", end="")
            if last_battery == 0:
                print(
                    " (⚠️  May indicate device needs charging or battery reading unavailable)"
                )
            else:
                print()

        # Rate assessment
        print("\n📈 Assessment:")
        if avg_rate >= 120:
            print("  ✅ Excellent polling rate (expected ~128 Hz)")
        elif avg_rate >= 100:
            print("  ✅ Good polling rate")
        elif avg_rate >= 80:
            print("  ⚠️  Moderate polling rate (some delays)")
        else:
            print("  ❌ Low polling rate (connection issues)")

        # Device is sending at 128Hz, we're reading latest only
        total_expected = elapsed * 128  # Device sends ~128 packets/sec
        if packets_received >= total_expected * 0.8:
            print("  ✅ Reading almost every packet (low skip rate)")
        elif packets_received >= total_expected * 0.5:
            print("  ⚠️  Reading some packets (moderate skip rate)")
        else:
            print(
                "  ⚠️  Reading few packets (high skip rate - normal if polling slowly)"
            )

        print()

    finally:
        # Clean up
        print("Stopping reader...")
        reader.stop()
        print("✅ Done!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
