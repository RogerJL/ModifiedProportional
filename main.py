# This is a sample Python script.

# Press Skift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import typing

UTSKOTT = 8


class Election:

    def __init__(self,
                 committee_name: str,  # name of commitee
                 group: list[str],  # Kyrkomötets nomineringsgrupper
                 mandates: list[int],  # Kyrkomötets ledamöter
                 presidium: list[int],  # Kyrkomötets precidium
                 board: list[int],  # Kyrkostyrelsens ordinarie
                 board_sup: list[int]  # Kyrkostyrelsens ersättare (ej ordinarie i utskott)
                 ):
        self.committee_name = committee_name
        self.group = group
        self.mandates = mandates
        self.presidium = presidium
        self.board = board
        self.board_sup = board_sup

class ModifiedProportional(Election):

    def __init__(self,
                 committee_name: str,  # name of commitee
                 group: list[str],  # Kyrkomötets nomineringsgrupper
                 mandates: list[int],  # Kyrkomötets ledamöter
                 presidium: list[int],  # Kyrkomötets precidium
                 board: list[int],  # Kyrkostyrelsens ordinarie
                 board_sup: list[int],  # Kyrkostyrelsens ersättare (ej ordinarie i utskott)
                 extra_allocation: list[int],  # Varje grupps önskade placeringar i detta utskott
                 ):
        super().__init__(committee_name, group, mandates, presidium, board, board_sup)
        self.elected = [0] * len(mandates)
        self.remaining = [0] * len(mandates)
        for index, m in enumerate(mandates):
            total = m - self.presidium[index] - self.board[index] - self.board_sup[index]
            self.remaining[index] = total // UTSKOTT + (1 if extra_allocation[index] and total % UTSKOTT > 0 else 0)
        print("Indata för", committee_name)
        for index, e in enumerate(self.elected):
            print(f"  '{self.group[index]}' {self.remaining[index]}")

    def process(self):
        print("Undelning utskott", self.committee_name)
        turn = 0
        done = False
        while not done:
            turn += 1
            best_index = self.determine_best()

            done = self.check_best(best_index, turn)
            if not done:
                self.place_best(best_index, turn)

        print()
        print("Resultat Utskott", self.committee_name)
        people_total_min = 0
        people_total_max = 0
        for g, s, e, r in zip(self.group, self.board_sup, self.elected, self.remaining):
            s_min = r
            s_max = min((r + s + UTSKOTT - 1) // UTSKOTT, r + s)
            s_text = str(s_min) if s_min == s_max else f"{s_min}..{s_max}"
            print(f"'{g}:\t{e} ledamöter med rösträtt,\tmed {s_text} ({r}+{s}) ersättare")
            people_total_max += e + s_max
            people_total_min += e + r
        print(f"Total utskotts storlek {people_total_min}..{people_total_max}")
        print()


    def determine_best(self) -> list[int]:
        best = 0.0
        best_index = None
        for index, m in enumerate(self.mandates):
            current = m / (self.elected[index] + 1)
            if current > best:
                best = current
                best_index = [index]
            elif not current < best:
                best_index.append(index)
        return best_index

    def check_best(self, best_index: list[int], turn: int):
        done = False
        for index in best_index:
            if self.remaining[index] == 0:
                print(
                    f"  #{turn} '{self.group[index]}' saknar i utskott placeringsbara ledamöter, har {self.board_sup[index]} fria ersättare")
                done = True
        return done

    def place_best(self, best_index: list[int], turn: int):
        prev_elected = sum(self.elected)
        if len(best_index) > 1 and (prev_elected < 15 <= prev_elected + len(best_index)):
            print("  Med 15 fasta ordinarie sker lottning mellan följande")
        for index in best_index:
            number = 1  # placera en åt gången
            if number > self.remaining[index]:
                print(
                    f"  #{turn}: '{self.group[index]}' saknar ledamöter (har {self.remaining[index]}) för placering i samtliga utskott")
                number = self.remaining[index]
            self.elected[index] += number
            self.remaining[index] -= number
            print(f"  #{turn}/{sum(self.elected)}: '{self.group[index]}' {self.elected[index]}, {self.remaining[index]}")
        if prev_elected < 15 <= sum(self.elected):
            print("  Med 15 fasta ordinarie och 15 fasta ersättare startar utdelning om från början",  prev_elected)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    group = ["Utl",	"AfS",	"S",	"BA",	"C",	"FiSK",	"FK",	"HoJ",	"KR",	"MPSKDG",	"POSK",	"SD",	"ViSK",	"ÖKA"]
    mandates =  [2, 3,	70,	20,	30,	4,	8,	1,	7,	8,	47,	19,	19,	13]
    presidium = [0,	0,	 1,  0,	 1,	0,	0,  0,  0,  0,   1,  0,  0,  0]
    board =     [0,	0,	 5,  1,	 2,	0,	1,  0,  0,  0,   3,  1,  1,  0]
    board_sup = [0,	0,	 4,  1,	 2,	0,	0,  0,  1,  1,   2,  1,  1,  1]

    ModifiedProportional("Maximum", group, mandates, presidium, board, board_sup, [True] * 14).process()
#    ModifiedProportional("Minimum", group, mandates, presidium, board, board_sup, [False] * 14).process()
    mixed = [True] * 14
    mixed[2] = False  # Socialdemokraterna not using all
    ModifiedProportional("Mixed", group, mandates, presidium, board, board_sup, mixed).process()

    ModifiedProportional("Organisations",
                         ["AfS",	"S+C+ViSK+ÖKA",		"POSK+BA+Utl+FK+KR+MPSKDG", 	"FiSK",		"HoJ",	"SD"],
                         [3, 132, 92, 4, 1, 19],
                         [0,   2,  1, 0, 0,  0],
                         [0,   8,  5, 0, 0,  1],
                         [0,   9,  6, 1, 1,  2],
                         [True] * 6)\
        .process()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
