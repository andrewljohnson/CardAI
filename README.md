This project lets you battle AIs against each other, that play a CCG-like card game. Or play vs. them yourself via CLI.

## Run the code.

By default, it will play a Monte Carlo Search Tree bot vs. a Human, with 20 life.

```
python battle-bots.py
```

You can change the defaults, for example to play two Monte Carlo Search Tree bots against each other with 10 starting life.

```
python battle-bots.py --players 1 1 --starting_hit_points 10
```



