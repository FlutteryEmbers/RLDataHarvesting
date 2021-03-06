from trainer.Q_Learning.ddqn import DDQN, MEMORY_CAPACITY
from environments import single_diescreteV1
from utils.tools import plot_curve
from utils.tools import Timer
from loguru import logger
                   

n_games = 2000
best_num_steps = 9999999999999999
best_rewards = 0 
episode_rewards = []
num_steps = []
timer = Timer()

env = None

DR = True
if DR:
    env = single_diescreteV1.DR_Environment
else:
    env = single_diescreteV1.Test_Environment

ddqn = DDQN(inputs=len(env.status_tracker.get_state()), outputs=env.action_space.n, env=env)

for i in range(n_games):
    logger.success('<<<<<<<<<Episode: %s' % i)
    s, current_position = env.reset()
    episode_reward_sum = 0

    timer.start()
    while True:
        # env.render()
        a = ddqn.choose_action(s, current_position)
        s_, r, done, current_position = env.step(a)

        ddqn.store_transition(s, a, r, s_, done)
        episode_reward_sum += r

        s = s_

        if ddqn.memory_counter > MEMORY_CAPACITY:
            ddqn.learn()

        if done:
            logger.success('episode%s---reward_sum: %s' % (i, round(episode_reward_sum, 2)))
            env.view()
            break
        
    num_steps.append(env.num_steps)

    if DR:
        ddqn.save_models(mode='DR')
    else:
        if env.num_steps < best_num_steps:
            best_num_steps = env.num_steps
            ddqn.save_models()
    episode_rewards.append(round(episode_reward_sum, 2))
    timer.stop()
        
x = [i+1 for i in range(n_games)]
plot_curve(x, episode_rewards, './results/rewards.png', 1)
plot_curve(x, num_steps, './results/step.png', 2)