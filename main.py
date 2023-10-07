# This is a sample Python script.

# Press Skift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import fractions
import logging
import typing

UTSKOTT = 8


def execute():
    groups = ["Utl", "AfS", "S", "BA", "C", "FiSK", "FK", "HoJ", "KR", "MPSKDG", "POSK", "SD", "ViSK", "ÖKA"]
    # Valresultat
    mandates = [2, 3, 70, 20, 30, 4, 8, 1, 7, 8, 47, 19, 19, 13]
    # Resultat av indirekta val
    presidium = [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0]
    board = [0, 0, 5, 1, 2, 0, 1, 0, 0, 0, 3, 1, 1, 0]
    board_sup = [0, 0, 4, 1, 2, 0, 0, 0, 1, 1, 2, 1, 1, 1]
    election2021 = Election(groups, mandates, presidium, board, board_sup)


    # Av respektive nomineringsgrupp valt antal ledamöter för detta utskott
    alloc_max = [1, 1, 8, 3, 4, 1, 1, 1, 1, 1, 6, 3, 3, 2]
    ModifiedProportional(election2021).group_requests("Maximum", alloc_max).process()
    #    alloc_min = [0, 0, 7, 2, 3, 0, 0, 0, 0, 0, 5, 2, 2, 1]
    #    ModifiedProportional("Minimum", groups, mandates, presidium, board, board_sup, alloc_min).process()
    alloc_mixed = alloc_max.copy()
    alloc_mixed[2] = 7  # Socialdemokraterna valde att ej använda alla
    ModifiedProportional(election2021).group_requests("Mixad", alloc_mixed).process()

    election2021coop = election2021.coop(["AfS", "S+C+ViSK+ÖKA", "POSK+BA+Utl+FK+KR+MPSKDG+FiSK", "HoJ", "SD"])
    print("Valsamverkan", election2021coop)
    alloc_coop = [1, 15, 11, 0, 2]
    ModifiedProportional(election2021coop).group_requests("Exempel med valsamverkan", alloc_coop).process()



class Election:

    def __init__(self,
                 group: list[str],  # Kyrkomötets nomineringsgrupper
                 mandates: list[int],  # Kyrkomötets ledamöter
                 presidium: list[int],  # Kyrkomötets precidium
                 board: list[int],  # Kyrkostyrelsens ordinarie
                 board_sup: list[int]  # Kyrkostyrelsens ersättare (ej ordinarie i utskott)
                 ):
        self.group = group
        self.mandates = mandates
        self.presidium = presidium
        self.board = board
        self.board_sup = board_sup

    def __str__(self):
        return "{" + str(self.group) \
            + "\nmandates=" + str(self.mandates) \
            + "\npresidium=" + str(self.presidium) \
            + "\nboard=" + str(self.board) \
            + "\nboard_sup=" + str(self.board_sup) + "}"

    def coop(self,
             among:list[str]):
        errors = 0
        mandates = []
        presidium = []
        board = []
        board_sup = []
        used = [0] * len(self.mandates)
        for groups in among:
            mandates_ = 0
            presidium_ = 0
            board_ = 0
            board_sup_ = 0
            for group in groups.split("+"):
                try:
                    index = self.group.index(group)
                    used[index] += 1
                    mandates_ +=  self.mandates[index]
                    presidium_ += self.presidium[index]
                    board_ += self.board[index]
                    logging.debug("%s: #%d board_sup=%d", group, index, self.board_sup[index])
                    board_sup_ += self.board_sup[index]
                except ValueError as e:
                    errors += 1
                    logging.error("Group name (%s) could not be found", group)
            mandates.append(mandates_)
            presidium.append(presidium_)
            board.append(board_)
            board_sup.append(board_sup_)
        for name, count in zip(self.group, used):
            if count == 0:
                errors += 1
                logging.error("Group (%s) is never used", name)
            if count > 1:
                errors += 1
                logging.error("Group (%s) is used more than once (%d)", name, count)
        if errors:
            exit(1)
        return Election(among, mandates, presidium, board, board_sup)

class ModifiedProportional:

    def __init__(self,
                 election: Election
                 ):
        self.prev_elected = election
        self.committee_name = None
        self.election = []
        self.remaining = []

    def group_requests(self,
                       committee_name: str,  # name of commitee,
                       allocation: list[int],  # Varje grupps önskade placeringar i detta utskott
                       ):
        self.committee_name = committee_name
        self.election = [0] * len(allocation)
        self.remaining = allocation.copy()  # TODO: replace with dict .values()

        print("Indata för", committee_name)
        elect = self.prev_elected
        errors = 0
        for index, r in enumerate(self.remaining):
            total = self.can_be_placed_with_voting_right(index)
            s_min = total // UTSKOTT
            s_max = s_min + (1 if total % UTSKOTT > 0 else 0)
            if r > s_max or r < s_min:
                errors += 1
                logging.error("'%s' har för kort eller lång namn lista (%d), antalet skall vara inom %d..%d",
                              elect.group[index], r, s_min, s_max)
                continue
            print(f"  '{elect.group[index]}' {r} ({s_min}..{s_max}) goal {100*elect.mandates[index]/(sum(elect.mandates)-2):.2f}%")
        if errors:
            exit(1)
        return self

    def can_be_placed_with_voting_right(self, index):
        elect = self.prev_elected
        total = elect.mandates[index] - elect.presidium[index] - elect.board[index] - elect.board_sup[index]
        return total

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
        for g, s, e, r in zip(self.prev_elected.group, self.prev_elected.board_sup, self.election, self.remaining):
            s_min = r + s // UTSKOTT
            s_max = min((r + s + UTSKOTT - 1) // UTSKOTT, r + s)
            s_text = str(s_min) if s_min == s_max else f"{s_min}..{s_max}"
            print(f"'{g}:\t{e} ledamöter med rösträtt ({100*e/(sum(self.election)):.2f}%),\tmed {s_text} ({r} kvar, {s} ers. ky.styr) ersättare")
            people_total_max += e + s_max
            people_total_min += e + s_min
        print(f"Total utskotts storlek {people_total_min}..{people_total_max}")
        print()


    def determine_best(self) -> list[int]:
        best = 0.0
        best_index = None
        for index, m in enumerate(self.prev_elected.mandates):
            current = fractions.Fraction(m, (self.election[index] + 1))
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
                group_ = self.prev_elected.group[index]
                sup_index_ = self.prev_elected.board_sup[index]
                print(
                    f"  #{turn} '{group_}' saknar fler i utskott placeringsbara ledamöter, har {sup_index_} ersättare från kyrkostyrelsen att fördela")
                done = True
        return done

    def place_best(self, best_index: list[int], turn: int):
        prev_election = sum(self.election)
        if len(best_index) > 1 and (prev_election < 15 <= prev_election + len(best_index)):
            print("  Med 15 fasta ordinarie sker lottning mellan följande")
        for index in best_index:
            number = 1  # placera en åt gången
            group_ = self.prev_elected.group[index]
            if number > self.remaining[index]:
                print(
                    f"  #{turn}: '{group_}' saknar ledamöter (har {self.remaining[index]}) för placering i samtliga utskott")
                number = self.remaining[index]
            comp = fractions.Fraction(self.prev_elected.mandates[index], self.election[index] + 1)
            self.election[index] += number
            self.remaining[index] -= number
            print(f"  #{turn}/{sum(self.election)}: '{group_}' {comp=} valda {self.election[index]}, kvar {self.remaining[index]}")
        if prev_election < 15 <= sum(self.election):
            print("  Med 15 fasta ordinarie och 15 fasta ersättare startar utdelning om från början",  prev_election)
            for index, e in enumerate(self.election):
                print(f"    '{self.prev_elected.group[index]}': {100*e/(sum(self.election)):.2f}%")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    execute()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
