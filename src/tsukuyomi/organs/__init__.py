"""The eight organs.

Four binary gates (Skin, Shoulders, Knee, Toe) and four continuous senses
(Ears, Eyes, Nose, Mouth). See docs/architecture/03_organs.md.
"""
from tsukuyomi.organs.skin import Skin
from tsukuyomi.organs.ears import Ears
from tsukuyomi.organs.shoulders import Shoulders
from tsukuyomi.organs.knee import Knee
from tsukuyomi.organs.toe import Toe
from tsukuyomi.organs.eyes import Eyes
from tsukuyomi.organs.nose import Nose
from tsukuyomi.organs.mouth import Mouth

__all__ = ["Skin", "Ears", "Shoulders", "Knee", "Toe", "Eyes", "Nose", "Mouth"]
