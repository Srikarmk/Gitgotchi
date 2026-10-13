"""Names, colors and voice for the Halloween theme."""
from dataclasses import dataclass

from gitgotchi.pet.states import PetForm, PetMood

ORANGE = "#ff8c1a"
PURPLE = "#a06cd5"
GREEN = "#8bd450"
BONE = "#f2e8cf"
CYAN = "#6ff5e0"
BLOOD = "#e5484d"
GOLD = "#ffd25a"
DIM = "#7d6b91"


@dataclass(frozen=True)
class FormInfo:
    title: str
    icon: str
    color: str
    blurb: str


FORMS = {
    PetForm.EGG: FormInfo(
        "Pumpkin", "🎃", ORANGE, "A tiny jack-o'-lantern. Feed it commits and see what hatches."
    ),
    PetForm.GHOST: FormInfo(
        "Ghost", "👻", BONE, "A friendly little spirit that floats around your repo."
    ),
    PetForm.ANGEL: FormInfo(
        "Angel", "😇", GOLD, "Clean commits, real tests. Your spirit earned its halo."
    ),
    PetForm.DEMON: FormInfo(
        "Demon", "😈", BLOOD, "Fed on vague messages and giant diffs. It likes the chaos."
    ),
    PetForm.ZOMBIE: FormInfo(
        "Zombie", "🧟", GREEN, "Too many reverts. It keeps coming back, like that bug."
    ),
    PetForm.WRAITH: FormInfo(
        "Wraith", "🌙", CYAN, "Fifteen commits deep. Nothing under the hood but two eyes."
    ),
    PetForm.POLTERGEIST: FormInfo(
        "Poltergeist", "👾", CYAN, "The agents write most of the code now. It feeds on their keystrokes."
    ),
}

MOODS = {
    PetMood.JOYFUL: ("glowing", "is glowing like a fresh jack-o'-lantern"),
    PetMood.HAPPY: ("cheerful", "is floating around happily"),
    PetMood.CONTENT: ("content", "is quietly haunting your repo"),
    PetMood.HUNGRY: ("hungry", "is hungry... it hasn't tasted a commit in a day"),
    PetMood.TIRED: ("fading", "is starting to fade. Three days without a commit"),
    PetMood.SLEEPING: ("dormant", "is dormant in its crypt. A commit would wake it"),
}

COMMIT_REACTIONS = [
    "{name} gobbled up your commit",
    "{name} cackles with delight",
    "Something stirs in the repo... {name} grows stronger",
    "{name} does a little spooky spin",
    "{name} adds your commit to its collection",
]

AGENT_REACTIONS = [
    "{agent} possessed this commit",
    "The keyboard typed itself... {agent} was here",
    "{name} felt a chill. {agent} wrote this one",
    "Spectral keystrokes from {agent}",
]

PET_REACTIONS = [
    "{name} wiggles happily",
    "{name} does a loop-de-loop",
    "{name} glows a little brighter",
    "{name} purrs. Ghosts can purr",
]

WAKE_REACTION = "{name} rises from its crypt, happy to see you"


def form_info(form: PetForm) -> FormInfo:
    return FORMS.get(form, FORMS[PetForm.GHOST])
