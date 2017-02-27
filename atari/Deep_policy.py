#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 19:59:26 2017

@author: shengx
"""

#%%
import tensorflow as tf
import numpy as np
import random
import gym
import matplotlib.pyplot as plt

DEBUG = True


RENDER = False  # if displaying game graphics real time
LEARNING_RATE = 0.001 

IMG_X, IMG_Y = 80, 80

#%% Deep Q-Network Structure
class DQNet():
    def __init__(self,input_size = (80, 80, 1), action_space = 3):

        self.input_x, self.input_y, self.input_frame= input_size
        self.action_space = action_space

    def build_nn(self):
        

        # [batch, in_height, in_width, in_channels]
        # assuming input to be batch_size*84*84*4
        
        self.input = tf.placeholder(tf.float32, shape = [None, 6400])
        
        ##################################################################
        self.conv1_W = tf.Variable(tf.truncated_normal([8, 8, 1, 32], 
                                                           stddev = 0.1))
        self.conv1_strides = [1, 4, 4, 1]
        self.conv1_out = tf.nn.conv2d(tf.reshape(self.input,[-1, 80, 80,1]), 
                                          self.conv1_W, 
                                          self.conv1_strides, 
                                          padding = 'SAME')
        self.conv1_out = tf.nn.relu(self.conv1_out)
        #output 20*20*32 
        
        
        ##################################################################
        self.conv2_W = tf.Variable(tf.truncated_normal([4, 4, 32, 64],
                                                           stddev = 0.1))
        self.conv2_strides = [1, 2, 2, 1]
        # output 9*9*64
        self.conv2_out = tf.nn.conv2d(self.conv1_out, 
                                          self.conv2_W, 
                                          self.conv2_strides, 
                                          padding = 'VALID')
        self.conv2_out = tf.nn.relu(self.conv2_out)        
        
        
        ##################################################################
        self.conv3_W = tf.Variable(tf.truncated_normal([3, 3, 64, 64],
                                                           stddev = 0.1))
        self.conv3_strides = [1, 1, 1, 1]
        # output 7*7*64
        self.conv3_out = tf.nn.conv2d(self.conv2_out, 
                                          self.conv3_W, 
                                          self.conv3_strides, 
                                          padding = 'VALID')
        self.dqn_conv3_out = tf.nn.relu(self.conv3_out)
        
        
        
        ##################################################################
        self.ff1_input = tf.reshape(self.dqn_conv3_out, [-1, 3136])
        self.ff1_W = tf.Variable(tf.truncated_normal([3136, 512],
                                                         stddev = 0.1))
        self.ff1_b = tf.Variable(tf.truncated_normal([1, 512],
                                                         stddev = 0.1))
        # output batch_size * 512
        self.ff1_out = tf.matmul(self.ff1_input, self.ff1_W) + self.ff1_b
        self.ff1_out = tf.nn.relu(self.ff1_out)
        
        
        ##################################################################
        self.ff2_W = tf.Variable(tf.truncated_normal([ 512, self.action_space],
                                                         stddev = 0.1))
        self.ff2_b = tf.Variable(tf.truncated_normal([ 1, self.action_space],
                                                         stddev = 0.1))
        # final output, batch_size * action_space
        self.ff2_out = tf.matmul(self.ff1_out, self.ff2_W) + self.ff2_b
        
        
        ##################################################################        
        self.output = tf.nn.softmax(self.ff2_out)
        
        self.predict_action = tf.argmax(self.output, axis = 1)
        
        self.advantage = tf.placeholder(tf.float32, shape=[None])
        self.actions = tf.placeholder(tf.int32, shape=[None])
        
        self.actions_onehot = tf.one_hot(self.actions, self.action_space, dtype=tf.float32)
        self.neg_log_prob =  -tf.multiply(self.actions_onehot * tf.log(self.output), tf.reshape(self.advantage, [-1, 1]))
        self.loss = tf.reduce_mean(self.neg_log_prob)
        
        self.update = tf.train.AdamOptimizer(learning_rate = LEARNING_RATE).minimize(self.loss)

#%%
batch_size = 32
x = np.random.random_sample((batch_size, 6400)).astype('float32')
y = np.random.randint(0, 3, (batch_size))
advantage = np.arange(32)/32

#%%

A = DQNet();
A.build_nn();
init_op = tf.global_variables_initializer()
sess = tf.Session()
sess.run(init_op)
#%%

sess.run(A.update, feed_dict={
        A.input: x,
        A.actions: y,
        A.advantage: advantage})


#%% utility functions

def process_frame(frame):
    # input a single frame
    # crop & downsample & average over 3 color channels 
    return np.mean(frame[34: 194 : 2, 0: 160 : 2, :], axis = 2, dtype = 'float32') > 100

gamma = 0.99
def discount_rewards(r):
  """ take 1D float array of rewards and compute discounted reward """
  discounted_r = np.zeros_like(r)
  running_add = 0
  for t in reversed(range(0, r.size)):
    if r[t] != 0: running_add = 0 # reset the sum, since this was a game boundary (pong specific!)
    running_add = running_add * gamma + r[t]
    discounted_r[t] = running_add
  return discounted_r


 
#%% initialize and running the model 

###################################################################
# initialize parameter
max_episode = 2
max_frame = 1000

frame_skip = 2
reward_decay = 0.99

###################################################################
# initialize replay memory buffer

buffer_size = 10000

###################################################################
# Set the game
env = gym.make("Pong-v0")

#%%


#%%
###################################################################
# training 
action_space = 3  # possible action = 1, 2, 3; still, up, down

max_episode = 21
max_frame = 10000
batch_size = 32
running_reward = None
future_reward_discount = 0.99
random_action_prob = 0.9





tf.reset_default_graph()
Atari_AI = DQNet()
Atari_AI.build_nn()


init_op = tf.global_variables_initializer()
sess = tf.Session()
sess.run(init_op)



save_frequency = 100
save_path = "/home/shengx/Documents/CheckpointData_policy_deep/"
saver = tf.train.Saver()
try:
    ckpt = tf.train.get_checkpoint_state(save_path)
    load_path = ckpt.model_checkpoint_path
    saver.restore(sess, load_path)
    print("Session restored...")
except:
    print("Nothing to restore...")


i_episode = 0

state = np.zeros((80, 80, 2),dtype = 'float32')
state_sequence, action_sequence, reward_sequence = [], [], []
while True:
    
    i_episode += 1
    
    state[:,:,0] = process_frame(env.reset())
    

    reward_sum = 0
    
    for t in range(max_frame):
        if RENDER:
            env.render()
        # select an action based on policy network output probability
        diff_frame = np.reshape(state[:,:,1] - state[:,:,0], (1, 6400))
        nn_prob = sess.run(Atari_AI.output, feed_dict={
                Atari_AI.input: diff_frame})
    
        action = np.random.choice(3, p=np.squeeze(nn_prob))
        # excute the action for a few steps
        for _ in range(frame_skip):
            observation, reward, done, info = env.step(action + 1)
            reward_sum += reward
            if done:
                break
        
        # update the new state and reward and memory buffer
        state[:,:,0] = state[:,:,1]
        state[:,:,1] = process_frame(observation) 
        
        state_sequence.append(diff_frame)
        action_sequence.append(action)
        reward_sequence.append(reward)
        
        
        # save the model after every 200 updates       
        if done:
            
            decay_reward = discount_rewards(np.vstack(reward_sequence).astype('float32'))
            s = np.vstack(state_sequence)
            a = np.vstack(action_sequence)
            
            decay_reward -= np.mean(decay_reward)
            decay_reward /= np.std(decay_reward)
            
            running_reward = reward_sum if running_reward is None else running_reward * 0.99 + reward_sum * 0.01
            
            sess.run(Atari_AI.update, feed_dict={
            Atari_AI.input: s,
            Atari_AI.actions: np.squeeze(a),
            Atari_AI.advantage:  np.squeeze(decay_reward)})

            state_sequence, action_sequence, reward_sequence = [], [], []
            
            
            if i_episode % 10 == 0:
                print('ep {}: reward: {}, mean reward: {:3f}'.format(i_episode, reward_sum, running_reward))
            else:
                print('\tep {}: reward: {}'.format(i_episode, reward_sum))
                
            if i_episode % save_frequency == 0:
                saver.save(sess, save_path+'model-'+str(i_episode)+'.cptk')
                print("SAVED MODEL #{}".format(i_episode)) 
            break
