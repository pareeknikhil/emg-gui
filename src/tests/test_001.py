import tensorflow as tf

embeddings = tf.constant([
    [1.,2.,3.],
    [2.,3.,4.],
    [3.,4.,5.],
    [4.,5.,6.],
    [5.,6.,7.],
    [6.,7.,8.],
    [7.,8.,9.],
    [8.,9.,10.]
], dtype=tf.float32)

distance_matrix = tf.expand_dims(embeddings, 1) - tf.expand_dims(embeddings, 0)
distance = tf.norm(distance_matrix, axis=2)

B = tf.shape(distance)[0]
eye = tf.eye(B, dtype=tf.bool)

tf.print(~eye)
