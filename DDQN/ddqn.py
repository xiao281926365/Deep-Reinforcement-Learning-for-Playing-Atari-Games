import tensorflow as tf
from params import Params

class DDQNet():
    def __init__(self, action_space):

        self.IMG_X = Params['IMG_X']
        self.IMG_Y = Params['IMG_Y']
        self.IMG_Z = Params['IMG_Z']
        self.action_space = action_space
        self.learning_rate = Params['LEARNING_RATE']
        self.primary_scope = 'primary'
        self.target_scope = 'target'
        
        self.reward_discount = 0.99
        
        self.dueling_nn()
        


    def dueling_nn(self):
        
        with tf.variable_scope(self.primary_scope) as scope:
            self.primary_in, self.primary_out = self.build_nn()
            
        with tf.variable_scope(self.target_scope) as scope:
            self.target_in, self.target_out = self.build_nn()
            

        self.end_game = tf.placeholder(shape=[None],dtype=tf.float32)
        self.current_reward = tf.placeholder(shape=[None],dtype=tf.float32)
        self.actions = tf.placeholder(shape=[None],dtype=tf.int32)
        
        next_Q = tf.reduce_max(self.target_out, axis = 1)
        
        targetQ = self.current_reward + self.reward_discount * tf.multiply(1 - self.end_game, next_Q)
        
        targetQ = tf.stop_gradient(targetQ)
                
        actions_onehot = tf.one_hot(self.actions, self.action_space, dtype=tf.float32)
        
        Q = tf.reduce_sum((self.primary_out * actions_onehot), reduction_indices=1)
        
        loss = tf.reduce_mean(tf.square(targetQ - Q))
        
        # training
        self.update = tf.train.AdamOptimizer(learning_rate = self.learning_rate).minimize(loss)
        # predict action according to the target network
        self.predict = tf.argmax(self.target_out, axis = 1)
        
        # synchronize two networks
        from_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.primary_scope)
        to_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.target_scope)
        self.sync_op = []
        for from_var, to_var in zip(from_variables, to_variables):
            self.sync_op.append(to_var.assign(from_var.value()))
        
        
    def build_nn(self):
        

        # [batch, in_height, in_width, in_channels]
        # assuming input to be batch_size*84*84*4
        state_in = tf.placeholder(tf.float32, shape=[None, self.IMG_X, self.IMG_Y, self.IMG_Z])
        state_resized = tf.image.resize_images(state_in, [80, 80])

        ##########################################################
        #[filter_height, filter_width, in_channels, out_channels]
        # conv layer 1, 8*8*32 filters, 4 stride
        conv1_W = tf.Variable(tf.truncated_normal([8, 8, self.IMG_Z, 32], stddev = 0.01))
        conv1_b = tf.Variable(tf.truncated_normal([1, 20, 20, 32], stddev = 0.01))
        conv1_strides = [1, 4, 4, 1]
        #output 20*20*32 
        conv1_out = tf.nn.conv2d(state_resized, conv1_W, conv1_strides, 
                                          padding = 'SAME') + conv1_b
        conv1_out = tf.nn.relu(conv1_out)
        
        
        ###########################################################
        # conv layer 2, 4*4*64 filters, 2 stride
        conv2_W = tf.Variable(tf.truncated_normal([4, 4, 32, 64], stddev = 0.01))
        conv2_b = tf.Variable(tf.truncated_normal([1, 9, 9, 64], stddev = 0.01))
        conv2_strides = [1, 2, 2, 1]
        # output 9*9*64
        conv2_out = tf.nn.conv2d(conv1_out, conv2_W, conv2_strides, 
                                          padding = 'VALID') + conv2_b
        conv2_out = tf.nn.relu(conv2_out)
       

        ###########################################################
        # fully connected layer 1, (7*7*64 = 3136) * 512
        ff1_input = tf.reshape(conv2_out, [-1, 5184])
        ff1_W = tf.Variable(tf.truncated_normal([5184, 256], stddev = 0.01))
        ff1_b = tf.Variable(tf.truncated_normal([1, 256], stddev = 0.01))
        # output batch_size * 512
        ff1_out = tf.matmul(ff1_input, ff1_W) + ff1_b
        ff1_out = tf.nn.relu(ff1_out)
        
        
        advantage_in, value_in = tf.split(ff1_out, 2, axis = 1)
        
        advantage_W = tf.Variable(tf.truncated_normal([128, self.action_space], stddev = 0.01))
        value_W = tf.Variable(tf.truncated_normal([128, 1], stddev = 0.01))
        
        advantage_out = tf.matmul(advantage_in, advantage_W)
        
        value_out = tf.matmul(value_in, value_W)
        
        #Then combine them together to get our final Q-values.
        Q_out = value_out + advantage_out - tf.reduce_mean(advantage_out,reduction_indices=1,keep_dims=True)
        
        return state_in, Q_out


    def sync_variables(self, sess):

        # adding scope to network        
        sess.run(self.sync_op)
            
    def train(self, sess, state_current, state_future, action, reward, end_game):
        
        sess.run(self.update, feed_dict={self.target_in: state_future,
                                         self.primary_in: state_current,
                                         self.actions: action,
                                         self.current_reward: reward,
                                         self.end_game: end_game})

    def predict_act(self, sess, state):
        # 1X80X80X4 single image
        action = sess.run(self.predict,
                          feed_dict = {self.target_in: state})
        return action
