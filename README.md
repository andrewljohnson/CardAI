This project lets you battle AIs that play a CCG-like card game, via command line. 

## Play Human vs AI, or AI vs AI

By default, it will play a Monte Carlo Search Tree bot vs. a Human, with 20 life.

```
python battle-bots.py
```

You can change the defaults, for example to play two Monte Carlo Search Tree bots against each other with 10 starting life.

```
python battle-bots.py --players 1 1 --starting_hit_points 10
```

## Example Run

```
➜  CardAI git:(master) ✗ python battle-bots.py                                        
# TURN 1 ################################################
> Player 1 (mcst) drew a card.
> Player 1 (mcst) played a Forest.
> Player 1 (mcst) summoned a 2/2 NettleSentinel.
# TURN 2 ################################################
> You drew Vines Of Vastwood.
  1: Play Forest
  return: Pass the Turn
  p: Print the game board.
Type the number of the action you want to play: p
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        20 life - Player 2 (mcst) - Mana Pool: []

         ----------- ----------- ----------- ----------- ----------- ----------- 
         |    *    | |    *    | |    *    | |    *    | |    *    | |    *    | 
         |  *   *  | |  *   *  | |  *   *  | |  *   *  | |  *   *  | |  *   *  | 
         |   * *   | |   * *   | |   * *   | |   * *   | |   * *   | |   * *   | 
         ----------- ----------- ----------- ----------- ----------- ----------- 
                                       TAPPED----- 
                                       |         | 
                                       | Forest  | 
                                       |         | 
                                       ----------- 
                                       ----------- 
                                       | G       | 
                                       | Net Sen | 
                                       | 2/2     | 
                                       ----------- 

                              ______________________________

----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- 
| G       | | G       | |         | | G       | | G       | |         | | RGRG    | | G       | 
| Qui Ran | | Hun Of  | | Forest  | | Vin Of  | | Ska Pit | | Forest  | | Bur Emi | | Vin Of  | 
| 1/1     | |         | |         | |         | | 1/1     | |         | | 2/2     | |         | 
----------- ----------- ----------- ----------- ----------- ----------- ----------- ----------- 

                         20 life - You - Mana Pool: []
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  1: Play Forest
  return: Pass the Turn
  p: Print the game board.
Type the number of the action you want to play: 
```
