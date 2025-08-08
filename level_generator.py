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
    config_file = 'randomgen.txt'
    
    # Read configuration
    with open(config_file, 'r') as f:
        start_level = int(f.readline().strip())
        num_to_generate = int(f.readline().strip())
        
    # Generate levels
    for i in range(num_to_generate):
        level_num = start_level + i
        generate_level(level_num)
        
    # Update the starting level number for the next run
    new_start_level = start_level + num_to_generate
    with open(config_file, 'w') as f:
        f.write(f"{new_start_level}\n")
        f.write(f"{num_to_generate}\n")
        
    print(f"\nGeneration complete. Next run will start from level {new_start_level}.")
