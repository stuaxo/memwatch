def eat_mb(mb):
    one_k='M' * 1024
    one_m=one_k * 1024
    for i in range(0, mb):
        b=one_m * i
        print '%s mb' % (i +1)


if __name__=='__main__':
    eat_mb(128) # use 128 mb



