import numpy as np
import random
from utils.buffer import Info
from numpy import linalg as LNG
from utils.tools import Timer
from environments.config import actions
from loguru import logger

timer = Timer()
# NOTE: Discrete Position; Single Agent
class Agent():
    def __init__(self, env, state_mode = 'MLP', action_type = 'Discrete', max_episode_steps = 10000):
        # self.reward_func = self.test_reward_function
        self._max_episode_steps = max_episode_steps
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
        # logger.debug(s)
        # return s, self.status_tracker.current_position
        return s
    
    def step(self, action, verbose = 0, type_reward = 'default'):
        if verbose > 0:
            logger.debug('angular representation: {}'.format(action))
        action = self.action_space.get_action(action)

        self.num_steps += 1

        current_position, tower_location, dv_collected, dv_left, dv_transmittion_rate, dv_required = self.status_tracker.get_current_status()
        
        position = self.status_tracker.update_position(action)
        if verbose > 0:
            logger.debug('action_take: {}'.format(action))
            logger.debug('current_position: {}'.format(position))
        # data_volume_collected, data_transmitting_rate_list = Phi_dif_transmitting_speed(self.status_tracker.current_position, tower_location, dv_collected, dv_required)
        # data_volume_left = np.array(dv_required) - np.array(data_volume_collected)
        data_volume_collected, data_transmitting_rate_list, data_volume_left = self.status_tracker.transmitting_model.update_dv_status(self.status_tracker.current_position, dv_collected, dv_required)

        self.status_tracker.update_dv_info(dv_collected=data_volume_collected, 
                                    dv_transmittion_rate=data_transmitting_rate_list, 
                                    dv_left=data_volume_left)

        self.running_info.store(position_t=position, action_t=action,
                                    data_collected_t=data_volume_collected, 
                                    data_left_t=data_volume_left, data_collect_rate_t = data_transmitting_rate_list)

        done = False
        if type_reward == 'default':  
            reward = self.status_tracker.get_reward()
            reward -= self.num_steps * 0.01 # ????????????reward 1

            # NOTE: ????????????????????????
            if self.status_tracker.is_done():
                reward -= 5 * LNG.norm(np.array(self.status_tracker.current_position) - np.array(self.status_tracker.arrival_at))
                done = True

        elif type_reward == 'HER':
            reward = -1
            if self.status_tracker.is_done() and np.array_equal(self.status_tracker.current_position, self.status_tracker.arrival_at):
                reward = 0
                done = True

        else:
            reward = -1
            if self.status_tracker.is_done():
                reward -= np.sum(np.array(self.status_tracker.current_position) - np.array(self.status_tracker.arrival_at))
                done = True

        s = self.status_tracker.get_state(mode = self.state_mode)
        return s, reward, done, self.status_tracker.current_position

    def view(self):
        logger.info('data left = {} steps taken = {}'.format(np.array(self.status_tracker.dv_required) - np.array(self.status_tracker.dv_collected), self.num_steps))
        return self.running_info