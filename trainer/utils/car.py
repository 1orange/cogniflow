import math
from config import *


class Car:
    """Represents the car in the trainer with pseudo-3D physics and movement capabilities."""

    def __init__(self, x=0, y=300, z=0):
        # Pseudo-3D position
        self.x = x  # Position along the road
        self.y = y  # Lateral position (left/right)
        self.z = z  # Height above road
        self.angle = 0  # Steering angle
        self.velocity = 0  # Forward/backward speed
        self.acceleration = 0  # Current acceleration

        # Legacy 2D properties for compatibility
        self.heading = -90.0  # in degrees
        self.speed = 0
        self.radius = 10

        # Load car sprite
        # sprite_path = os.path.join(os.path.dirname(__file__), "..", "assets", "m2.png")
        # self.sprite = pg.image.load(sprite_path).convert()
        # self.sprite.set_colorkey((255, 0, 255))
        # self.sprite_rect = self.sprite.get_rect()

    def update(self, dt, commands=None):
        """Update car position based on multiple commands and time delta using pseudo-3D physics."""
        if commands is None:
            commands = []

        # Apply drag to acceleration and velocity
        self.acceleration += -PLAYER_DRAG_FACTOR * self.acceleration * dt
        self.velocity += -PLAYER_DRAG_FACTOR * self.velocity * dt

        # Process multiple commands simultaneously
        for command in commands:
            match command:
                case "left":
                    self.angle -= dt * self.velocity / PLAYER_STEERING_FACTOR
                case "right":
                    self.angle += dt * self.velocity / PLAYER_STEERING_FACTOR
                case "forward":
                    if self.velocity > -1:
                        self.acceleration += PLAYER_ACCELERATION_FORCE * dt
                    else:
                        self.acceleration = 0
                        self.velocity += -self.velocity * dt
                case "backward":
                    if self.velocity < 1:
                        self.acceleration -= PLAYER_BRAKE_FORCE * dt
                    else:
                        self.acceleration = 0
                        self.velocity += -self.velocity * dt

        # Clamp values to valid ranges
        self.velocity = max(
            PLAYER_MIN_VELOCITY, min(self.velocity, PLAYER_MAX_VELOCITY)
        )
        self.angle = max(PLAYER_MIN_ANGLE, min(PLAYER_MAX_ANGLE, self.angle))

        # Apply acceleration to velocity
        self.velocity += self.acceleration * dt

        # Update position based on velocity and angle
        self.x += self.velocity * dt * math.cos(self.angle)
        self.y += self.velocity * math.sin(self.angle) * dt * 100

        # Update legacy properties for compatibility
        self.speed = abs(self.velocity)
        self.heading = math.degrees(self.angle)

    def wrap_around(self, screen_width, screen_height):
        """Wrap car position around screen edges."""
        self.x = (self.x + screen_width) % screen_width
        self.y = (self.y + screen_height) % screen_height

    def draw(self, screen):
        """Draw the car sprite on the screen."""
        # Rotate the sprite based on heading
        # Note: pygame rotates counter-clockwise, so we need to negate the heading
        # rotated_sprite = pg.transform.rotate(self.sprite, -self.heading)
        # rotated_rect = rotated_sprite.get_rect()

        # Center the sprite on the car's position
        # rotated_rect.center = (int(self.x), int(self.y))
        self.sprite_rect.center = (int(self.x), int(self.y))

        # Draw the rotated sprite
        screen.blit(self.sprite, self.sprite_rect)
