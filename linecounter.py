import os, sys, mmap, functools, multiprocessing as mp
from tqdm import tqdm          # <-- only new import

root = r'C:\Users\you\Desktop\Webscout'
workers = mp.cpu_count()

def count_in_file(path):
    with open(path, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        return m.read().count(b'\n')

if __name__ == '__main__':
    py_files = [os.path.join(d, name)
                for d, _, files in os.walk(root)
                for name in files if name.endswith('.py')]
    with mp.Pool(workers) as pool:
        total = sum(tqdm(pool.imap(count_in_file, py_files, chunksize=64),
                         total=len(py_files), unit='file'))
    print('Total lines:', total)