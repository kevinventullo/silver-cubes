def check(cube):
    problem = False
    for i in range(11):
        for j in range(11):
            for k in range(11):
                if ((i + j + k)%11 == 0):
                    set_coll = set()
                    set_coll.add(cube[i][j][k])
                    for l in range(1,11):
                        set_coll.add(cube[(i+l)%11][j][k])
                        set_coll.add(cube[i][(j+l)%11][k])
                        set_coll.add(cube[i][j][(k+l)%11])
                    if (len(set_coll) != 31):
                        print('Problem at ', i, ',',j,',',k)
                        problem = True
    if not problem:
        print('No problem!')



def main():
    cube = []
    with open('silver_z2_n11_h16x6_cadical.txt', 'r') as f:
        line = f.readline()
        for j in range(11):
            line = f.readline()
            line = f.readline()
            square = []
            for i in range(11):
                line = f.readline()
                linearr = [int(x) for x in line.split()]
                square.append(linearr)
            cube.append(square)
    print(cube)
    print(check(cube))




            

if __name__ == "__main__":
    main()