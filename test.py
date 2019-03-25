from tict import Tict

d = Tict()
d[1] = 2
d[3] = 4
del d[1]
print(dict(d))
# print(d[1])
d[1] = 3
print(dict(d))

print(d._keyvals)

state = d.save()
d[1] = 10
d[2] = 20
state2 = d.save()
d[4] = 40
del d[3]
print(dict(d))


d.rollback(state2)

print(dict(d))

d2 = d.copy()
d.rollback(state)

print(dict(d))


d[1] = 10
d[2] = 20
d[4] = 40
del d[3]

# d.rollback(state2)

print(dict(d.copy()))
print(dict(d2))

# print(d2._keyvals)
d2.revert(state)
print(dict(d2))
# print(d2._keyvals)
d2.rollback(state)
print(dict(d2))
