import pygame
import pymunk
import pymunk.pygame_util
from StickFigure import StickFigure
import time
import math
from Button import Button

last_interaction = time.time()
RESET_TIMEOUT = 1

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
fps = 60
space = pymunk.Space()
space.gravity = (0, 900)
space.sleep_time_threshold = 0.5  # enable sleeping!

draw_options = pymunk.pygame_util.DrawOptions(screen)

def is_figure_at_start(figure, threshold=5):
    head_pos = figure.head.position
    start_pos = figure.start_position
    dx = head_pos[0] - start_pos[0]
    dy = head_pos[1] - start_pos[1]
    distance_sq = dx*dx + dy*dy
    return distance_sq < threshold*threshold


def add_boundaries(space, width, height, thickness=5):
    static_lines = [
        pymunk.Segment(space.static_body, (0, height - thickness), (width, height - thickness), thickness),
        pymunk.Segment(space.static_body, (0, 0), (0, height), thickness),
        pymunk.Segment(space.static_body, (width, 0), (width, height), thickness),
        pymunk.Segment(space.static_body, (0, 0), (width, 0), thickness),
    ]
    for line in static_lines:
        line.elasticity = 0.8
        line.friction = 0.5
        space.add(line)

add_boundaries(space, 800, 600)

# Create the stick figure
figure = StickFigure(space, (400, 200))

# Gravity simulation
simulate_gravity_rotation = False
gravity_angle = 0  # Radians
gravity_magnitude = 900
font = pygame.font.SysFont(None, 24)

def toggle_gravity_sim():
    global simulate_gravity_rotation
    simulate_gravity_rotation = not simulate_gravity_rotation

gravity_button = Button(rect=(680, 10, 110, 30), text="Toggle Gravity", font=font, callback=toggle_gravity_sim)

def draw_gravity_arrow(surface, gravity, origin=(400, 300), scale=0.05, color=(255, 0, 0)):
    end_x = origin[0] + gravity[0] * scale
    end_y = origin[1] + gravity[1] * scale
    pygame.draw.line(surface, color, origin, (end_x, end_y), 4)
    
    # Draw arrowhead
    angle = math.atan2(gravity[1], gravity[0])
    arrow_size = 10
    left = (end_x - arrow_size * math.cos(angle - math.pi / 6),
            end_y - arrow_size * math.sin(angle - math.pi / 6))
    right = (end_x - arrow_size * math.cos(angle + math.pi / 6),
             end_y - arrow_size * math.sin(angle + math.pi / 6))
    pygame.draw.polygon(surface, color, [(end_x, end_y), left, right])


def reset_figure_and_gravity():

    
    global gravity_angle, simulate_gravity_rotation, space
    gravity_angle = 0
    simulate_gravity_rotation = False
    space.gravity = (0, gravity_magnitude)  # Reset gravity to default downward vector

    figure.reset()

reset_button = Button(rect=(560, 10, 110, 30), text="Reset Figure", font=font, callback=reset_figure_and_gravity)


running = True
while running:
    current_time = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pymunk.pygame_util.from_pygame(event.pos, screen)
            
            if not simulate_gravity_rotation:
                figure.handle_mouse_down(mouse_pos)
            
            last_interaction = current_time

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if not simulate_gravity_rotation:
                figure.handle_mouse_up()
            
            last_interaction = current_time


        elif event.type == pygame.MOUSEMOTION:
            last_interaction = current_time  # reset timer on mouse move
        
        gravity_button.handle_event(event)
        reset_button.handle_event(event)


    mouse_pos = pymunk.pygame_util.from_pygame(pygame.mouse.get_pos(), screen)

    if not simulate_gravity_rotation:
        figure.handle_mouse_move(mouse_pos)

    max_velocity = 1000
    for body in figure.bodies:
        if body.velocity.length > max_velocity:
            body.velocity = body.velocity.normalized() * max_velocity

    if simulate_gravity_rotation:
        gravity_angle += 0.01
        gravity_angle = gravity_angle % (2 * math.pi)  # ✅ Keep angle bounded
        gx = gravity_magnitude * math.sin(gravity_angle)
        gy = gravity_magnitude * math.cos(gravity_angle)
        space.gravity = (gx, gy)

    max_velocity = 1000
    for body in figure.bodies:
        if body.velocity.length > max_velocity:
            body.velocity = body.velocity.normalized() * max_velocity

    space.step(1 / fps)
    screen.fill((255, 255, 255))

    # Draw stick figure
    figure.draw(screen)
    
    # Draw UI
    gravity_button.draw(screen)

    # Display gravity vector
    gravity_text = font.render(f"Gravity: ({space.gravity[0]:.1f}, {space.gravity[1]:.1f})", True, (0, 0, 0))
    screen.blit(gravity_text, (10, 10))

    # Top-center origin for gravity arrow
    origin = (screen.get_width() // 2, 80)  

    draw_gravity_arrow(screen, space.gravity, origin=origin)

    label = font.render("Gravity Direction", True, (255, 0, 0))
    screen.blit(label, (origin[0] - 60, origin[1] - 25))  # Centered above the arrow

    reset_button.draw(screen)

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()
