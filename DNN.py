import tensorflow as tf
from datahelper import *


class DNN:
    def __init__(self, batch_num, embedding_size, genre_matrix, genre_size=genre_count, occ_size=occ_count, geo_size=geo_count,
                 l2_reg_lamda=0.0):
        self.g = tf.placeholder(tf.int64, [batch_num])
        self.a = tf.placeholder(tf.float64, [batch_num])
        self.o = tf.placeholder(tf.int64, [batch_num])
        self.geo = tf.placeholder(tf.int64, [batch_num])
        self.wh = tf.placeholder(tf.int64, [batch_num, None])
        self.time = tf.placeholder(tf.int64, [batch_num])
        self.y = tf.placeholder(tf.int64, [batch_num, 1])

        self.genre_Query = genre_matrix

        self.genre_emb_w = tf.Variable(tf.random_uniform([genre_size, embedding_size], -1.0, 1.0))
        self.occupation_emb_w = tf.Variable(tf.random_uniform([occ_size, embedding_size], -1.0, 1.0))
        self.geographic_emb_w = tf.Variable(tf.random_uniform([geo_size, embedding_size], -1.0, 1.0))
        # embedding process
        with tf.name_scope("embedding"):
            watch_genre = tf.gather(self.genre_Query, self.wh)
            watch_history_genre_emb = tf.nn.embedding_lookup(self.genre_emb_w, watch_genre)
            watch_history_final = tf.reduce_mean(tf.reduce_mean(watch_history_genre_emb, axis=1),axis=1)

            geo_emb = tf.nn.embedding_lookup(self.geographic_emb_w, self.geo)
            occ_emb = tf.nn.embedding_lookup(self.occupation_emb_w, self.o)

        user_vector = tf.concat([geo_emb, occ_emb, watch_history_final, tf.stack([self.g, self.a, self.time], axis=1)],
                                axis=1)

        # Deep Neural Network
        with tf.name_scope("layer"):
            d_layer_1 = tf.layers.dense(user_vector, units=1024, activation=tf.nn.relu, use_bias=True, name='f1',
                                        trainable=True)
            d_layer_2 = tf.layers.dense(d_layer_1, units=512, activation=tf.nn.relu, use_bias=True, name='f2',
                                        trainable=True)
            d_layer_3 = tf.layers.dense(d_layer_2, units=256, activation=tf.nn.relu, use_bias=True, name='f3',
                                        trainable=True)
        movie_embedding = tf.Variable(
            tf.truncated_normal([movie_count, embedding_size], steddev=1.0 / math.sqrt(embedding_size)), trainable=True)
        biases = tf.Variable(tf.zeros([movie_count]))

        with tf.name_scope("loss"):
            if mode == 'train':
                self.loss = tf.reduce_mean(
                    tf.nn.sampled_softmax_loss(movie_embedding, biases, self.y, d_layer_3,
                                               num_sampled=100, num_classes=movie_count, num_true=1,
                                               partition_strategy="div"
                                               ))
            elif mode == 'eval':
                logits = tf.matmul(d_layer_3, tf.transpose(movie_embedding))
                logits = tf.nn.bias_add(logits, biases)
                labels_one_hot = tf.one_hot(self.y, movie_count)
                self.loss = tf.nn.softmax_cross_entropy_with_logits_v2(
                    labels=labels_one_hot,
                    logits=logits)
