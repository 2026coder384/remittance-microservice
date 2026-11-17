Secret_number = 2
guess_count = 0

while guess_count < 3:
    guess = int(input("Guess: "))
    guess_count = guess_count + 1
    if guess == Secret_number:
        print("you won! ")
        break
else:
    print("Sorry you guessed wrong number")
