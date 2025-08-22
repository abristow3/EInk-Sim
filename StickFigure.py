import pygame
import pymunk.pygame_util
import time

class StickFigure:
    def __init__(self, space, position):
        self.space = space
        self.start_position = position  # base offset
        self.bodies = []
        self.joints = []
        self.dragging = False
        self.drag_joint = None
        self.drag_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.space.add(self.drag_body)

        # Define fixed local offsets for upright pose relative to start_position
        x, y = position
        self.reference_positions = {
            'head': (x, y),
            'torso_top': (x, y + 30),
            'torso_bottom': (x, y + 60),
            'left_hand': (x - 25, y + 30),
            'right_hand': (x + 25, y + 30),
            'left_foot': (x - 15, y + 90),
            'right_foot': (x + 15, y + 90),
        }

        self._create_figure()
        self.freeze()

    # In _create_circle(), detect body part and optionally increase mass
    def _create_circle(self, pos, radius=10, mass=0.5):
        if 'torso' in str(pos):  # crude check, or pass label
            mass *= 2  # double torso mass

        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = pos
        shape = pymunk.Circle(body, radius)
        shape.friction = 0.5
        self.space.add(body, shape)
        self.bodies.append(body)
        return body

    def _connect_with_limits(self, a, b, min_angle, max_angle):
        """Connect two bodies with a pivot and angle limits"""
        pivot = pymunk.PivotJoint(a, b, a.position)
        limit = pymunk.RotaryLimitJoint(a, b, min_angle, max_angle)
        self.space.add(pivot, limit)
        self.joints.extend([pivot, limit])

    def _create_figure(self):
        pos = self.reference_positions

        self.head = self._create_circle(pos['head'])
        self.torso_top = self._create_circle(pos['torso_top'])
        self.torso_bottom = self._create_circle(pos['torso_bottom'])
        self.left_hand = self._create_circle(pos['left_hand'])
        self.right_hand = self._create_circle(pos['right_hand'])
        self.left_foot = self._create_circle(pos['left_foot'])
        self.right_foot = self._create_circle(pos['right_foot'])

        # Connect joints as before with limits
        self._connect_with_limits(self.head, self.torso_top, -0.2, 0.2)
        self._connect_with_limits(self.torso_top, self.torso_bottom, -0.1, 0.1)
        self._connect_with_limits(self.torso_top, self.left_hand, -1.5, 0.5)
        self._connect_with_limits(self.torso_top, self.right_hand, -0.5, 1.5)
        self._connect_with_limits(self.torso_bottom, self.left_foot, -0.5, 1)
        self._connect_with_limits(self.torso_bottom, self.right_foot, -1, 0.5)



    def handle_mouse_down(self, mouse_pos):
        shape = list(self.head.shapes)[0]
        if shape.point_query(mouse_pos).distance <= 0:
            self.unfreeze()     # wake up on drag
            self.dragging = True
            self.drag_body.position = mouse_pos
            self.drag_joint = pymunk.PivotJoint(self.drag_body, self.head, (0, 0), (0, 0))
            self.drag_joint.max_force = 5000
            self.drag_joint.error_bias = (1 - 0.15) ** 60
            self.space.add(self.drag_joint)



    def handle_mouse_up(self):
        """Stop dragging"""
        if self.dragging and self.drag_joint:
            self.space.remove(self.drag_joint)
            self.drag_joint = None
        self.dragging = False

    def handle_mouse_move(self, mouse_pos):
        """Move the drag body if dragging"""
        if self.dragging:
            self.drag_body.position = mouse_pos
    
    def draw(self, surface):
        def to_pygame(pos):
            return pymunk.pygame_util.to_pygame(pos, surface)

        # Draw limbs as lines
        BLACK = (0, 0, 0)
        width = 4

        pygame.draw.line(surface, BLACK, to_pygame(self.head.position), to_pygame(self.torso_top.position), width)
        pygame.draw.line(surface, BLACK, to_pygame(self.torso_top.position), to_pygame(self.torso_bottom.position), width)

        pygame.draw.line(surface, BLACK, to_pygame(self.torso_top.position), to_pygame(self.left_hand.position), width)
        pygame.draw.line(surface, BLACK, to_pygame(self.torso_top.position), to_pygame(self.right_hand.position), width)

        pygame.draw.line(surface, BLACK, to_pygame(self.torso_bottom.position), to_pygame(self.left_foot.position), width)
        pygame.draw.line(surface, BLACK, to_pygame(self.torso_bottom.position), to_pygame(self.right_foot.position), width)

        # Draw head as a circle
        head_pos = to_pygame(self.head.position)
        pygame.draw.circle(surface, BLACK, (int(head_pos[0]), int(head_pos[1])), 12, width)
    
    def reset(self):
        """Reset all bodies to their fixed upright pose, zero velocities, and freeze."""
        for name, body in [('head', self.head),
                        ('torso_top', self.torso_top),
                        ('torso_bottom', self.torso_bottom),
                        ('left_hand', self.left_hand),
                        ('right_hand', self.right_hand),
                        ('left_foot', self.left_foot),
                        ('right_foot', self.right_foot)]:
            target_pos = self.reference_positions[name]
            body.position = target_pos
            body.velocity = (0, 0)
            body.angular_velocity = 0
            body.force = (0, 0)
            body.torque = 0

        self.freeze()


    
    def freeze(self):
        """Stop all motion and put bodies to sleep."""
        for body in self.bodies:
            body.velocity = (0, 0)
            body.angular_velocity = 0
            body.force = (0, 0)
            body.torque = 0
            body.sleep()

    def unfreeze(self):
        """Wake up bodies to enable movement."""
        for body in self.bodies:
            body.activate()
