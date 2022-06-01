from multiprocessing import Pool


def main():
    with Pool(5) as p:
        print(p.starmap(f, [(1,1), (2,4), (3,2)]))  # starmap_async


def f(x,y):
    return x*y


if __name__ == '__main__':
    main()