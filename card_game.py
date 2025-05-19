import random

def create_deck():
    """Creates a deck of 52 cards as a list of (rank, suit) tuples."""
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
    # Create one card per suit and rank combination
    return [(rank, suit) for suit in suits for rank in ranks]

def card_value(card):
    """Returns a numeric value for the card, used for comparing card strength."""
    rank, _ = card
    rank_values = {
        '2': 2, '3': 3, '4': 4, '5': 5,
        '6': 6, '7': 7, '8': 8, '9': 9,
        '10': 10, 'Jack': 11, 'Queen': 12,
        'King': 13, 'Ace': 14
    }
    return rank_values[rank]

def play_high_card():
    # Create and shuffle the deck.
    deck = create_deck()
    random.shuffle(deck)
    
    # Each player draws one card.
    player1_card = deck.pop()  
    player2_card = deck.pop()
    
    print(f"Player 1 draws: {player1_card[0]} of {player1_card[1]}")
    print(f"Player 2 draws: {player2_card[0]} of {player2_card[1]}")
    
    # Compare the card values.
    if card_value(player1_card) > card_value(player2_card):
        print("Player 1 wins!")
    elif card_value(player2_card) > card_value(player1_card):
        print("Player 2 wins!")
    else:
        print("It's a tie!")

if __name__ == '__main__':
    play_high_card()
    
