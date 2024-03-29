import tensorflow.contrib.eager as tfe
import tensorflow as tf
import random
import argparse
import os
import sys

from episode import Episode
from policy import Policy
import config



def train(num_episodes=1000, 
          save_every=100, 
          checkpoint_dir="checkpoints",
          tensorboard_dir="tensorboard",
          tboard_every=10,
          find_target_prop = 0
          ):
    pol = Policy()
    writer = tf.contrib.summary.create_file_writer(tensorboard_dir)
    for j in range(1, num_episodes+1):
        random_secret = random.randint(0, config.max_guesses - 1)
        e = Episode(pol, random_secret, find_target_prop, True)
        history = e.generate()

        print("Episode:{}, length: {}".format(j, len(history)))

        G = -1 

        optimizer = \
            tf.train.GradientDescentOptimizer(
                learning_rate=config.reinforce_alpha*G)

        for i in reversed(range(1, len(history))):
            history_so_far = history[:i]
            next_action, _ = history[i]
            with tfe.GradientTape() as tape:
                action_logits = pol(history_so_far, with_softmax=False)
                loss = tf.nn.softmax_cross_entropy_with_logits_v2(
                    labels=tf.one_hot(
                        tf.convert_to_tensor([next_action]),
                        config.max_guesses),
                    logits=action_logits
                )

            grads = tape.gradient(loss, pol.variables)
            optimizer.apply_gradients(zip(grads, pol.variables))

            G -= 1
            optimizer._learning_rate = G * config.reinforce_alpha
            optimizer._learning_rate_tensor = None
            # hack. Should be able to pass a callable as learning_rate, see
            # https://www.tensorflow.org/api_docs/python/tf/train/GradientDescentOptimizer#args
            # can I perhaps submit a PR to fix this bug?

            sys.stdout.write("{}/{}\r".format(len(history)-i, len(history)))

        if j % save_every == 0 or j == num_episodes:
            saver = tfe.Saver(pol.named_variables)
            save_path = os.path.join(checkpoint_dir, 
                                     "episode{}".format(
                                         str(j).zfill(len(str(num_episodes)))))
            saver.save(save_path)

        if j % tboard_every == 0:
            with writer.as_default():
                with tf.contrib.summary.always_record_summaries():
                    tf.contrib.summary.scalar('total_return', 
                                              tf.convert_to_tensor([G]), 
                                              step=j)
    return pol


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description="Train the mastermind model "
    #                                  "Using the REINFORCE policy gradient "
    #                                  "method")
    # parser.add_argument("--num_episodes", 
    #                     help="Number of episodes to use for training",
    #                     type=int, default=1000)
    # parser.add_argument("--find_target_proba", 
    #                     help="proba of getting the right target in the trainning",
    #                     type=float, default=0)                    
    # parser.add_argument("--save_every", type=int, default=100,
    #                     help="Checkpoint every N episodes")
    # parser.add_argument("--checkpoint_dir", help="Checkpoint directory",
    #                     default="checkpoints")
    # parser.add_argument("--board_dir", help="Tensorboard directory",
    #                     default="tensorboard")
    # parser.add_argument("--tboard_every", type=int, default=10,
    #                     help="Write to tensorboard every N episodes")
    # args = parser.parse_args()
                                  
    # train(args.num_episodes, args.save_every, args.checkpoint_dir,
    #       args.board_dir, args.tboard_every)
    pol = train(num_episodes=5, 
          save_every=100, 
          checkpoint_dir="checkpoints0",
          tensorboard_dir="tensorboard0",
          tboard_every=10,
          find_target_prop = 0.5
          )
