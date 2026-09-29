import random
import numpy as np
import os
import pickle

def _to_bool_map(m):
    m = np.asarray(m)
    if m.dtype != np.bool_:
        if not ((m == 0) | (m == 1)).all():
            raise ValueError('compact_maps requires a strictly binary local map')
        m = m.astype(np.bool_)
    return m


class ReplayMemory:
    def __init__(self, capacity, seed, compact_maps=False):
        self.rng = random.Random(seed)
        self.capacity = capacity
        self.buffer = []
        self.position = 0
        # SCREEN-028 (default off): store the binary local maps as bool (1 byte instead of 4) and
        # restore float32 on sampling. Values are exactly 0/1 either way, so sampled batches equal
        # the float32-storage ones bit for bit; only host RAM and checkpoint size shrink 4x.
        self.compact_maps = compact_maps

    def push(self, map_state, rob_state, action, reward, next_map_state, next_rob_state, done):
        if self.compact_maps:
            map_state, next_map_state = _to_bool_map(map_state), _to_bool_map(next_map_state)
        if len(self.buffer) < self.capacity:
            self.buffer.append(None)
        self.buffer[self.position] = (map_state, rob_state, action, reward, next_map_state, next_rob_state, done)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        batch = self.rng.sample(self.buffer, batch_size)
        map_state, rob_state, action, reward, next_map_state, next_rob_state, done = map(np.stack, zip(*batch))
        if self.compact_maps:
            map_state, next_map_state = map_state.astype(np.float32), next_map_state.astype(np.float32)
        return map_state, rob_state, action, reward, next_map_state, next_rob_state, done

    def __len__(self):
        return len(self.buffer)

    def save_buffer(self, env_name, suffix="", save_path=None):
        if not os.path.exists('checkpoints/'):
            os.makedirs('checkpoints/')

        if save_path is None:
            save_path = "checkpoints/sac_buffer_{}_{}".format(env_name, suffix)
        print('Saving buffer to {}'.format(save_path))

        with open(save_path, 'wb') as f:
            pickle.dump(self.buffer, f)

    def load_buffer(self, save_path):
        print('Loading buffer from {}'.format(save_path))

        with open(save_path, "rb") as f:
            self.buffer = pickle.load(f)
            self.position = len(self.buffer) % self.capacity
