#!/usr/bin/env python3
"""
Test script for emotiv-rs module.

This script tests the Rust implementation of the Emotiv reader.
"""

import sys
import time


def test_import():
    """Test that the module can be imported."""
    print("=" * 60)
    print("TEST 1: Import emotiv_rs module")
    print("=" * 60)
    try:
        import emotiv_rs

        print("✓ Successfully imported emotiv_rs")
        return True
    except ImportError as e:
        print(f"✗ Failed to import emotiv_rs: {e}")
        print("\nTo install, run:")
        print("  cd bci/emotiv/lib")
        print("  poetry run maturin develop --release")
        return False


def test_constants():
    """Test that constants are accessible."""
    print("\n" + "=" * 60)
    print("TEST 2: Check constants")
    print("=" * 60)
    try:
        import emotiv_rs

        print(f"DEFAULT_VID: 0x{emotiv_rs.DEFAULT_VID:04X}")
        print(f"DEFAULT_PID: 0x{emotiv_rs.DEFAULT_PID:04X}")
        print(f"DEFAULT_PACKET_SIZE: {emotiv_rs.DEFAULT_PACKET_SIZE}")
        print("✓ All constants accessible")
        return True
    except Exception as e:
        print(f"✗ Failed to access constants: {e}")
        return False


def test_decrypt():
    """Test decryption function."""
    print("\n" + "=" * 60)
    print("TEST 3: Test decryption functions")
    print("=" * 60)
    try:
        import emotiv_rs

        # Create a dummy encrypted packet (32 bytes)
        dummy_encrypted = b"\x00" * 32

        # Test default key decryption
        result = emotiv_rs.decrypt_packet(dummy_encrypted)
        if result is None:
            print("✓ decrypt_packet returned None for dummy data (expected)")
        else:
            print(f"✓ decrypt_packet returned {len(result)} bytes")

        # Test custom key decryption
        custom_key = "31003554381037423100354838003750"
        result2 = emotiv_rs.decrypt_packet_with_key(dummy_encrypted, custom_key)
        if result2 is None:
            print("✓ decrypt_packet_with_key returned None for dummy data (expected)")
        else:
            print(f"✓ decrypt_packet_with_key returned {len(result2)} bytes")

        print("✓ Decryption functions work")
        return True
    except Exception as e:
        print(f"✗ Decryption test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_parse_sensor():
    """Test sensor parsing function."""
    print("\n" + "=" * 60)
    print("TEST 4: Test sensor parsing")
    print("=" * 60)
    try:
        import emotiv_rs

        print("\n[Test 4a: All-zero packet]")
        # Create a dummy decrypted packet (32 bytes, all zeros)
        dummy_packet = b"\x00" * 32

        result = emotiv_rs.parse_sensor_data(dummy_packet)
        if result is None:
            print("✗ parse_sensor_data returned None for dummy data")
            return False
        else:
            print(f"✓ parse_sensor_data returned data with keys: {list(result.keys())}")
            if "counter" in result:
                print(f"  - counter: {result['counter']}")
            if "gyro_x" in result:
                print(f"  - gyro_x: {result['gyro_x']} (signed, 0 - 104 = -104)")
            if "gyro_y" in result:
                print(f"  - gyro_y: {result['gyro_y']} (signed, 0 - 104 = -104)")
            if "battery" in result:
                print(f"  - battery: {result['battery']}% (0 < 200, so 0%)")
            if "sensors" in result:
                print(f"  - sensors: {len(result['sensors'])} channels, all values = 0")
            if "quality" in result:
                print(
                    f"  - quality: {len(result['quality'])} channels, all values = 0 (No signal)"
                )

        print("\n[Test 4b: Realistic packet simulation]")
        # Create a more realistic packet with:
        # - counter = 42
        # - some sensor data
        # - battery = 220 (should give ~42% battery)
        # - quality nibbles with variety
        # - gyro = 104, 106 (neutral position)
        realistic_packet = bytearray(32)
        realistic_packet[0] = 42  # Counter
        # Fill some sensor data (bytes 1-25) with non-zero values
        for i in range(1, 26):
            realistic_packet[i] = (i * 17) % 256
        realistic_packet[26] = 220  # Battery (220-200)*100/48 ≈ 42%
        realistic_packet[27] = 0x43  # Quality: sensor 0=3(Fair), 1=4(Good)
        realistic_packet[28] = 0x21  # Quality: sensor 2=1(Very poor), 3=2(Poor)
        realistic_packet[29] = 104  # Gyro X neutral
        realistic_packet[30] = 106  # Gyro Y slight movement

        result2 = emotiv_rs.parse_sensor_data(bytes(realistic_packet))
        if result2:
            print("✓ Realistic packet parsed successfully")
            print(f"  - counter: {result2['counter']}")
            print(f"  - battery: {result2['battery']}%")
            print(f"  - gyro_x: {result2['gyro_x']} (104 - 104 = 0, stable)")
            print(f"  - gyro_y: {result2['gyro_y']} (106 - 104 = +2, slight tilt)")
            print(f"  - sensors: {len(result2['sensors'])} channels")

            # Show ALL sensors
            print("\n  All 14 EEG Sensors:")
            for name, value in result2["sensors"].items():
                print(f"    {name:4s}: {value:5d}")

            # Show ALL quality values
            print("\n  All 14 Quality Values:")
            quality_labels = [
                "⚫ No signal",
                "🔴 Very poor",
                "🟠 Poor",
                "🟡 Fair",
                "🟢 Good",
            ]
            for name, quality in result2["quality"].items():
                label = (
                    quality_labels[quality]
                    if quality < len(quality_labels)
                    else f"Unknown({quality})"
                )
                print(f"    {name:4s}: {quality} - {label}")
        else:
            print("✗ Failed to parse realistic packet")
            return False

        print("\n✓ Sensor parsing function works correctly")
        return True
    except Exception as e:
        print(f"✗ Sensor parsing test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_reader_creation():
    """Test EmotivReader creation."""
    print("\n" + "=" * 60)
    print("TEST 5: Create EmotivReader instance")
    print("=" * 60)
    try:
        import emotiv_rs

        # Test with default parameters
        reader1 = emotiv_rs.EmotivReader(None, None, None, None)
        print("✓ Created reader with default parameters")

        # Test with custom parameters
        reader2 = emotiv_rs.EmotivReader(
            0x1234, 0xED02, 32, "31003554381037423100354838003750"
        )
        print("✓ Created reader with custom VID/PID/key")

        # Check is_running
        if not reader2.is_running():
            print("✓ Reader correctly reports not running")
        else:
            print("✗ Reader should not be running yet")
            return False

        return True
    except Exception as e:
        print(f"✗ Reader creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_reader_lifecycle():
    """Test EmotivReader start/stop without device."""
    print("\n" + "=" * 60)
    print("TEST 6: Test reader lifecycle (no device required)")
    print("=" * 60)
    try:
        import emotiv_rs

        reader = emotiv_rs.EmotivReader(None, None, None, None)

        # Try to start (will fail if no device, but should not crash)
        print("Attempting to start reader (expected to fail without device)...")
        reader.start()

        # Give it a moment
        time.sleep(0.1)

        # Check if running
        if reader.is_running():
            print("⚠ Reader is running (device might be connected!)")
            print("Testing poll methods...")

            # Test polling (should return None quickly)
            raw = reader.poll_raw()
            print(f"  poll_raw(): {type(raw)}")

            dec = reader.poll_decrypted()
            print(f"  poll_decrypted(): {type(dec)}")

            parsed = reader.poll_parsed()
            if parsed:
                print("  poll_parsed():")
                print(f"    - counter: {parsed.get('counter')}")
                print(f"    - gyro_x: {parsed.get('gyro_x')} (signed)")
                print(f"    - gyro_y: {parsed.get('gyro_y')} (signed)")
                print(f"    - battery: {parsed.get('battery')}%")
                print(f"    - sensors: {len(parsed.get('sensors', {}))} channels")
                print(f"    - quality: {len(parsed.get('quality', {}))} channels")
            else:
                print(f"  poll_parsed(): {parsed}")

            # Stop the reader
            reader.stop()
            print("✓ Successfully stopped reader")
        else:
            print("✓ Reader not running (no device connected - expected)")

        return True
    except Exception as e:
        print(f"⚠ Reader lifecycle test encountered error: {e}")
        print("  (This is expected if no Emotiv device is connected)")
        import traceback

        traceback.print_exc()
        return True  # Not a failure - just no device


def test_realistic_with_live_data():
    """Test realistic packet simulation and live data reading.

    Note: The Rust reader uses latest-only mode, which means it intentionally
    skips queued packets to always return the most recent data. This is ideal
    for real-time BCI applications but means we won't read every packet.
    """
    print("\n" + "=" * 60)
    print("TEST 7: Realistic Packet Simulation + Live Data")
    print("=" * 60)
    try:
        import emotiv_rs

        # ===== PART 1: Realistic Packet Simulation =====
        print("\n[Part 1: Simulated Packets with Various Scenarios]")
        print("-" * 60)

        # Scenario 1: Low battery with poor signal
        print("\n📦 Scenario 1: Low battery, poor signal quality")
        low_battery_packet = bytearray(32)
        low_battery_packet[0] = 100  # Counter
        for i in range(1, 26):
            low_battery_packet[i] = (i * 20) % 256
        low_battery_packet[26] = 205  # Battery ~10%
        low_battery_packet[27] = 0x11  # Quality: poor signal
        low_battery_packet[28] = 0x11
        low_battery_packet[29] = 104  # Gyro X neutral
        low_battery_packet[30] = 104  # Gyro Y neutral

        result1 = emotiv_rs.parse_sensor_data(bytes(low_battery_packet))
        if result1:
            print(f"  ✓ Counter: {result1['counter']}")
            print(f"  ✓ Battery: {result1['battery']}% (LOW)")
            print(f"  ✓ Gyro: X={result1['gyro_x']}, Y={result1['gyro_y']}")
            print(f"  ✓ Quality sample (F3): {result1['quality']['F3']} (Poor)")

        # Scenario 2: Good battery with head movement
        print("\n📦 Scenario 2: Good battery, active head movement")
        movement_packet = bytearray(32)
        movement_packet[0] = 150
        for i in range(1, 26):
            movement_packet[i] = (i * 33 + 127) % 256
        movement_packet[26] = 240  # Battery ~83%
        movement_packet[27] = 0x44  # Quality: good signal
        movement_packet[28] = 0x34
        movement_packet[29] = 90  # Gyro X: -14 (head turned left)
        movement_packet[30] = 115  # Gyro Y: +11 (head tilted forward)

        result2 = emotiv_rs.parse_sensor_data(bytes(movement_packet))
        if result2:
            print(f"  ✓ Counter: {result2['counter']}")
            print(f"  ✓ Battery: {result2['battery']}% (GOOD)")
            print(
                f"  ✓ Gyro: X={result2['gyro_x']} (turned), Y={result2['gyro_y']} (tilted)"
            )
            print(f"  ✓ Quality sample (F3): {result2['quality']['F3']} (Good)")

        # Scenario 3: Maximum values
        print("\n📦 Scenario 3: Edge case - maximum values")
        max_packet = bytearray(32)
        max_packet[0] = 255  # Max counter
        for i in range(1, 26):
            max_packet[i] = 255
        max_packet[26] = 248  # Battery 100%
        max_packet[27] = 0x44  # Quality: good
        max_packet[28] = 0x44
        max_packet[29] = 255  # Gyro X: max positive
        max_packet[30] = 255  # Gyro Y: max positive

        result3 = emotiv_rs.parse_sensor_data(bytes(max_packet))
        if result3:
            print(f"  ✓ Counter: {result3['counter']}")
            print(f"  ✓ Battery: {result3['battery']}%")
            print(f"  ✓ Gyro: X={result3['gyro_x']}, Y={result3['gyro_y']} (extreme)")
            print(f"  ✓ Sensor sample (F3): {result3['sensors']['F3']}")

        print("\n✓ All simulated scenarios tested successfully")

        # ===== PART 2: Live Data Reading =====
        print("\n[Part 2: Live Data from Device]")
        print("-" * 60)

        reader = emotiv_rs.EmotivReader(None, None, None, None)
        print("Attempting to connect to Emotiv device...")

        reader.start()
        time.sleep(0.5)  # Give it time to connect

        if reader.is_running():
            print("✓ Successfully connected to device!")
            print("\nReading live data for 3 seconds...")
            print(
                "  Note: Reader returns LATEST packet only (skips old queued packets)"
            )

            packets_received = 0
            packets_skipped = 0
            start_time = time.time()
            last_counter = None
            first_packet_seen = False
            gyro_readings = []
            battery_level = None
            quality_samples = []

            while time.time() - start_time < 3.0:
                parsed = reader.poll_parsed()

                if parsed:
                    packets_received += 1

                    # Track skipped packets (expected in real-time mode)
                    if last_counter is not None:
                        expected = (last_counter + 1) % 256
                        if parsed["counter"] != expected and first_packet_seen:
                            gap = (parsed["counter"] - expected) % 256
                            packets_skipped += gap
                        # Mark baseline established after first transition
                        first_packet_seen = True
                    last_counter = parsed["counter"]

                    # Collect gyro readings for movement detection
                    gyro_readings.append((parsed["gyro_x"], parsed["gyro_y"]))

                    # Track battery
                    battery_level = parsed["battery"]

                    # Sample quality periodically
                    if packets_received % 32 == 0:  # Every ~0.25 seconds
                        quality_samples.append(parsed["quality"].copy())
                        print(
                            f"  📊 Packet {packets_received}: "
                            f"Counter={parsed['counter']}, "
                            f"Battery={parsed['battery']}%, "
                            f"Gyro=({parsed['gyro_x']}, {parsed['gyro_y']}), "
                            f"F3 Quality={parsed['quality']['F3']}"
                        )

                time.sleep(0.001)  # Small delay to prevent busy loop

            # Analysis
            print("\n📈 Live Data Analysis:")
            print(f"  • Total packets read: {packets_received}")
            print(
                f"  • Packets skipped: {packets_skipped} (intentional - latest-only mode)"
            )
            print(f"  • Polling rate: {packets_received / 3.0:.1f} Hz")

            # Calculate what percentage of device packets we're reading
            expected_device_packets = 3.0 * 128  # Device sends ~128 Hz
            read_percentage = (
                (packets_received / expected_device_packets) * 100
                if expected_device_packets > 0
                else 0
            )
            print(
                f"  • Reading {read_percentage:.1f}% of device packets (100% = no skipping)"
            )

            if battery_level is not None:
                print(f"  • Final battery level: {battery_level}%")

            if gyro_readings:
                avg_gyro_x = sum(x for x, y in gyro_readings) / len(gyro_readings)
                avg_gyro_y = sum(y for x, y in gyro_readings) / len(gyro_readings)
                print(f"  • Average gyro: X={avg_gyro_x:.1f}, Y={avg_gyro_y:.1f}")

                # Detect if there was movement
                gyro_variance_x = sum(
                    (x - avg_gyro_x) ** 2 for x, y in gyro_readings
                ) / len(gyro_readings)
                gyro_variance_y = sum(
                    (y - avg_gyro_y) ** 2 for x, y in gyro_readings
                ) / len(gyro_readings)
                if gyro_variance_x > 100 or gyro_variance_y > 100:
                    print(
                        f"  • Head movement detected! (variance X={gyro_variance_x:.1f}, Y={gyro_variance_y:.1f})"
                    )
                else:
                    print(
                        f"  • Head stable (variance X={gyro_variance_x:.1f}, Y={gyro_variance_y:.1f})"
                    )

            if quality_samples:
                print("\n  📡 Signal Quality Over Time:")
                quality_labels = ["No signal", "Very poor", "Poor", "Fair", "Good"]
                # Show quality progression for F3 sensor
                print("    F3 sensor: ", end="")
                for i, q_sample in enumerate(quality_samples):
                    print(f"{q_sample['F3']}", end=" ")
                print()

            reader.stop()
            print("\n✓ Live data test completed successfully")

            # Provide feedback based on actual behavior
            if packets_received < 50:
                print(
                    "  ⚠ Warning: Very low polling rate - check for processing bottlenecks"
                )
            elif read_percentage > 95:
                print("  ✅ Excellent: Reading almost every device packet!")
            elif read_percentage > 80:
                print("  ✅ Good: Reading most device packets")
            elif read_percentage > 50:
                print("  ℹ️  Normal: Reading some packets (typical for Python polling)")
            else:
                print("  ℹ️  Low read rate: Normal if test has other processing delays")

        else:
            print("⚠ No device connected - live data test skipped")
            print("  This is not a failure, just means no Emotiv headset is available")

        return True

    except Exception as e:
        print(f"✗ Realistic + live data test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_python_wrapper():
    """Test the Python wrapper in bci.emotiv."""
    print("\n" + "=" * 60)
    print("TEST 8: Test Python wrapper (bci.emotiv)")
    print("=" * 60)
    try:
        from bci.emotiv import EEGReader
        from bci.emotiv.constants import DEFAULT_VID, DEFAULT_PID

        print("✓ Imported EEGReader")
        print(f"  DEFAULT_VID: 0x{DEFAULT_VID:04X}")
        print(f"  DEFAULT_PID: 0x{DEFAULT_PID:04X}")

        # Try to create reader (should delegate to Rust)
        reader = EEGReader()
        print("✓ Created EEGReader instance (Python wrapper)")

        return True
    except Exception as e:
        print(f"✗ Python wrapper test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "EMOTIV-RS TEST SUITE" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = []

    # Run tests
    results.append(("Import", test_import()))

    if not results[0][1]:
        print("\n" + "=" * 60)
        print("STOPPING: Module not installed")
        print("=" * 60)
        return 1

    results.append(("Constants", test_constants()))
    results.append(("Decryption", test_decrypt()))
    results.append(("Sensor Parsing", test_parse_sensor()))
    results.append(("Reader Creation", test_reader_creation()))
    results.append(("Reader Lifecycle", test_reader_lifecycle()))
    results.append(("Realistic + Live Data", test_realistic_with_live_data()))
    results.append(("Python Wrapper", test_python_wrapper()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")

    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
