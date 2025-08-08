import random
import os

def generate_level(level_num):
    level_objects = []
    level_width = 4000

    # Add ground
    level_objects.append(f"ground,0,580,{level_width},20")

    # Add start and goal
    start_x = random.randint(100, 200)
    level_objects.append(f"start,{start_x},540,40,50")
    
    goal_x = random.randint(level_width - 300, level_width - 100)
    goal_y = random.randint(100, 500)
    level_objects.append(f"goal,{goal_x},{goal_y},80,80")

    last_x = start_x
    last_y = 540

    # Generate a path of platforms and challenges
    while last_x < goal_x - 200:
        # Determine the next position
        next_x = last_x + random.randint(100, 250)
        next_y = last_y + random.randint(-150, 150)
        next_y = max(100, min(500, next_y)) # Clamp within screen bounds

        # Add a platform at the new position
        platform_w = random.randint(80, 200)
        level_objects.append(f"platform,{next_x},{next_y},{platform_w},20")

        # Decide whether to add a challenge between the last platform and this one
        challenge_type = random.choice(["none", "spike_trap", "3d_wall_puzzle", "trampoline_jump", "slope_path"])
        
        if challenge_type == "spike_trap" and next_x > last_x + 150:
            gap_center = (last_x + next_x) // 2
            spike_count = random.randint(2, 5)
            for i in range(spike_count):
                level_objects.append(f"spike,{gap_center - (spike_count//2)*20 + i*20},580,20,20")

        elif challenge_type == "3d_wall_puzzle":
            wall_x = (last_x + next_x) // 2
            wall_y = next_y - 100
            if wall_y > 100:
                 level_objects.append(f"wall_3d,{wall_x},{wall_y},20,100")
                 # Place a platform "behind" the wall, only reachable in 2D
                 level_objects.append(f"platform,{wall_x - 60},{wall_y + 80},80,20")

        elif challenge_type == "trampoline_jump":
            if last_y > 300: # Only place trampolines on lower platforms
                trampoline_x = last_x + random.randint(20, 50)
                level_objects.append(f"trampoline,{trampoline_x},{last_y - 20},80,20")

        elif challenge_type == "slope_path":
            slope_x = last_x + platform_w
            slope_y = last_y - 100
            if slope_y > 100:
                level_objects.append(f"slope,{slope_x},{slope_y},100,100,100,0") # Slope up
                level_objects.append(f"platform,{slope_x + 100},{slope_y},100,20")


        last_x = next_x
        last_y = next_y

    # Fill in some empty spaces with decorative platforms or walls
    for _ in range(random.randint(10, 20)):
        px = random.randint(100, level_width - 100)
        py = random.randint(100, 560)
        ptype = random.choice(["platform", "wall_3d"])
        if ptype == "platform":
            level_objects.append(f"platform,{px},{py},{random.randint(50,100)},20")
        else:
            level_objects.append(f"wall_3d,{px},{py},20,{random.randint(50,120)}")


    # Create the levels directory if it doesn't exist
    if not os.path.exists('levels'):
        os.makedirs('levels')
        
    # Save the level to a file
    level_name = f"random{level_num}.txt"
    with open(os.path.join('levels', level_name), 'w') as f:
        for obj_str in level_objects:
            f.write(obj_str + '\n')
            
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
