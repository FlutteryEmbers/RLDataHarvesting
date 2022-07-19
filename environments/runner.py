from environments.instances.single_diescreteV1 import DR_Environment, Test_Environment
from trainer.Q_Learning.ddqn import DDQN
from utils import tools

class DDQN_GameAgent():
    def __init__(self, mode = 'Default') -> None:
        # self.n_games = n_games
        self.mode = mode
        self.timer = tools.Timer()
        self.episode_rewards = []
        self.num_steps = []

    def run(self, env = Test_Environment):
        self.ddqn = DDQN(inputs=len(env.status_tracker.get_state()), outputs=env.action_space.n, env=env)
        self.ddqn.load_models(mode=self.mode)
        done = False
        s, current_position = env.reset()
        episode_reward_sum = 0

        while not done:
            a = self.ddqn.choose_action(s, current_position, disable_exploration=True)
            s_, r, done, current_position = env.step(a)

            self.ddqn.store_transition(s, a, r, s_, done)
            episode_reward_sum += r

            s = s_

        stats = env.view()
        stats.save(self.mode + "/")

    def train(self, n_games, mode = 'Default'):
        best_num_steps = float('inf')
        best_rewards = 0
        
        env = None
        if mode == 'Default':
            env = Test_Environment
        elif mode == 'DR':
            env = DR_Environment
        self.ddqn = DDQN(inputs=len(env.status_tracker.get_state()), outputs=env.action_space.n, env=env)

        for i in range(n_games):
            print('<<<<<<<<<Episode: %s' % i)
            s, current_position = env.reset()
            episode_reward_sum = 0

            self.timer.start()
            while True:
                # env.render()
                a = self.ddqn.choose_action(s, current_position)
                s_, r, done, current_position = env.step(a)

                self.ddqn.store_transition(s, a, r, s_, done)
                episode_reward_sum += r

                s = s_

                if self.ddqn.memory_counter > self.ddqn.memory.mem_size:
                    self.ddqn.learn()

                if done:
                    print('episode%s---reward_sum: %s' % (i, round(episode_reward_sum, 2)))
                    env.view()
                    break
                
            self.num_steps.append(env.num_steps)

            if self.mode == 'DR':
                self.ddqn.save_models(mode=mode)
            elif self.mode == 'Default':
                if env.num_steps < best_num_steps:
                    best_num_steps = env.num_steps
                    self.ddqn.save_models(mode=mode)
            self.episode_rewards.append(round(episode_reward_sum, 2))
            self.timer.stop()

        x = [i+1 for i in range(n_games)]
        tools.plot_curve(x, self.episode_rewards, 'results/' + mode + '/rewards.png')
        tools.plot_curve(x, self.num_steps, 'results/' + mode + '/step.png')
        