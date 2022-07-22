import numpy as np
import random
from utils.buffer import Info
from numpy import linalg as LNG
from utils.tools import Timer
from environments.config import actions

timer = Timer()
# NOTE: Discrete Position; Single Agent
class Agent():
    def __init__(self, env, state_mode = 'MLP', action_type = 'Discrete'):
        # self.reward_func = self.test_reward_function
        self._max_episode_steps = 10000
        self.state_mode = state_mode
        self.status_tracker = env
        self.action_type = action_type

        if self.action_type == 'Discrete':
            self.action_space = actions.Discrete()       
        else:
            self.action_space = actions.Continuous()

        self.running_info = Info(board_structure=self.status_tracker, num_turrent=self.status_tracker.num_tower)
        
        self.reward = 0
        self.num_steps = 0

    def reset(self):
        self.reward = 0
        self.num_steps = 0

        self.status_tracker.reset()
        self.running_info.reset()

        s = self.status_tracker.get_state(mode = self.state_mode)
        return s, self.status_tracker.current_position
    
    def step(self, action):
        if self.action_type == 'Discrete':
            action = self.action_space.get_indexed_action(action)

        self.num_steps += 1

        current_position, tower_location, dv_collected, dv_left, dv_transmittion_rate, dv_required = self.status_tracker.get_current_status()

        next_position = np.array(current_position) + np.array(action)
        self.status_tracker.update_position(next_position)
        
        # data_volume_collected, data_transmitting_rate_list = Phi_dif_transmitting_speed(self.status_tracker.current_position, tower_location, dv_collected, dv_required)
        # data_volume_left = np.array(dv_required) - np.array(data_volume_collected)
        data_volume_collected, data_transmitting_rate_list, data_volume_left = self.status_tracker.transmitting_model.update_dv_status(self.status_tracker.current_position, dv_collected, dv_required)

        self.status_tracker.update_dv_info(dv_collected=data_volume_collected, 
                                    dv_transmittion_rate=data_transmitting_rate_list, 
                                    dv_left=data_volume_left)

        self.running_info.store(position_t=self.status_tracker.current_position, action_t=action,
                                    data_collected_t=data_volume_collected, 
                                    data_left_t=data_volume_left, data_collect_rate_t = data_transmitting_rate_list)

        reward = self.status_tracker.get_reward()
        reward -= self.num_steps * 0.01 # 每步减少reward 1

        # NOTE: 判断是否到达终点
        if self.status_tracker.is_done():
            reward -= 5 * LNG.norm(np.array(self.status_tracker.current_position) - np.array(self.status_tracker.arrival_at))

        s = self.status_tracker.get_state(mode = self.state_mode)
        return s, reward, self.status_tracker.is_done(), self.status_tracker.current_position

    def view(self):
        print('data left = ', np.array(self.status_tracker.dv_required) - np.array(self.status_tracker.dv_collected), 'steps taken = ', self.num_steps)
        return self.running_info