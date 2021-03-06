import tensorflow as tf
import numpy as np
import gym

from dpn import DPNet
from logger import Logger
from params import Params

  
class Agent():
    
    def __init__(self):

        self.env = gym.make(Params['GAME'])
        
        # setting up parameters
        self.frame_skip = Params['FRAME_SKIP']
        self.reward_discount = Params['REWARD_DISCOUNT']
        self.IMG_X = Params['IMG_X']
        self.IMG_Y = Params['IMG_Y']
        
        self.action_space = self.env.action_space.n
        self.updates = 0
        
        
        self.nn = DPNet(self.action_space)

        # initialize variables    
        self.sess = tf.Session()
        self.saver = tf.train.Saver()
        self.sess.run(tf.global_variables_initializer())
        
        # restore variables
        self.logger = Logger(self.sess, self.saver)
        self.logger.restore()
           

    def run(self):
        
        while True:
            
            reward_sum = 0
            observation = self.env.reset()
            state_sequence = []
            action_sequence = []
            reward_sequence = []
            
            state = np.zeros((self.IMG_X, self.IMG_Y, 4), dtype = 'float32')
            state[:,:,-1] = self.process_frame(observation)

            while True:
                # select an action based on the predicted policy
                current_state = np.expand_dims(state[:,:,-1] - state[:,:,-2], axis = 2)
                observation, action, reward, done = self.take_action(current_state)
                reward_sum += reward
                
                # save the current state
                state_sequence.append(current_state)
                action_sequence.append(action)
                reward_sequence.append(reward)
                
                # update the new state and reward
                state = np.roll(state, -1, axis = 2)
                state[:, :, -1] = self.process_frame(observation)
                
                # save the model after every 200 updates       
                if done:
                    self.update_nn(state_sequence, action_sequence, reward_sequence)
                    self.logger.log(reward_sum)                    
                    break
                

    def take_action(self, current_state):
        
        # take an action according to the policy
        action_policy = self.nn.predict_policy(self.sess, np.expand_dims(current_state, axis = 0))
        
        action = np.random.choice(self.action_space, p=np.squeeze(action_policy))

        # excute the action for a few steps
        reward = 0
        for _ in range(self.frame_skip):
            observation, reward_temp, done, info = self.env.step(action)
            reward += reward_temp
            if done:
                break  
        return (observation, action, reward, done)
    
    def update_nn(self, states, actions, rewards):
        # calculate future discounted rewards
        future_rewards = np.zeros((len(rewards)))
        running_add = 0
        for t in reversed(range(0, len(rewards))):
            if rewards[t] != 0: running_add = 0
            running_add = running_add * self.reward_discount + rewards[t]
            future_rewards[t] = running_add
            
        self.nn.train(self.sess, states, actions, future_rewards)
        
            
    def test(self):
        while True:
            
            observation = self.env.reset()

            state = np.zeros((1, self.IMG_X, self.IMG_Y, 4), dtype = 'float32')
            state[0, :,:,-1] = self.process_frame(observation)

            while True:
                self.env.render()
                # select an action based on the predicted policy
                observation, action, reward, done = self.take_action(state)
            
                # update the new state and reward
                state = np.roll(state, -1, axis = 3)
                state[0, :, :, -1] = self.process_frame(observation)
                
                # save the model after every 200 updates       
                if done:                   
                    break
                
    def process_frame(self, frame):
        #frame_gray = frame * np.array(([0.21, 0.72, 0.07])) / 256
        # output shape 105X80
        return np.mean(frame[::2,::2], axis = 2, dtype = 'float32') / 256
    
    
    def reset_game(self):
        pass
