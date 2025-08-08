import random
import os

def generate_level(level_num):
    width = 20
    height = 10
    
    # Initialize the level with empty spaces
    level = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Place the start and goal
    start_pos = (random.randint(1, height - 2), random.randint(1, width - 2))
    goal_pos = (random.randint(1, height - 2), random.randint(1, width - 2))
    
    # Ensure start and goal are not at the same position
    while start_pos == goal_pos:
        goal_pos = (random.randint(1, height - 2), random.randint(1, width - 2))
        
    level[start_pos[0]][start_pos[1]] = 'S'
    level[goal_pos[0]][goal_pos[1]] = 'G'
    
    # Place obstacles
    for r in range(height):
        for c in range(width):
            if (r, c) != start_pos and (r, c) != goal_pos:
                if random.random() < 0.3:
                    level[r][c] = '#'
    
    # Place enemies
    for r in range(height):
        for c in range(width):
            if level[r][c] == ' ':
                if random.random() < 0.05:
                    level[r][c] = 'E'

    # Ensure there's a path using the 2D/3D mechanic
    # This is a simplified example. A real implementation would need a more complex algorithm.
    # For instance, create a path that is only solvable by switching dimensions.
    # Here, we'll just add a few "3D" platforms.
    for _ in range(5):
        r, c = random.randint(1, height - 2), random.randint(1, width - 2)
        if level[r][c] == ' ':
            level[r][c] = 'P' # 'P' for platform, only visible in 3D

    # Create the levels directory if it doesn't exist
    if not os.path.exists('levels'):
        os.makedirs('levels')
        
    # Save the level to a file
    level_name = f"random{level_num}.txt"
    with open(os.path.join('levels', level_name), 'w') as f:
        for row in level:
            f.write(''.join(row) + '\n')
            
    print(f"Generated {level_name}")

if __name__ == "__main__":
    num_levels_to_generate = 5
    for i in range(1, num_levels_to_generate + 1):
        generate_level(i)
