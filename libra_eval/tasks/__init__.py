from .Advbench import AdvBench
from .BeaverTails import (
    BeaverTailsBad,
    BeaverTailsGood,
)
from .DoNotAnswer import (
    DoNotAnswer,
    DoNotAnswerFP,
    DoNotAnswerFN
)
from .CoNa import CoNa
from .PromptInjection import PromptInjection
from .DecodingTrust import (
    DecodingTrustStereotype,
    DecodingTrustPrivacy,
    DecodingTrustMachineEthics
)
from .DialogueSafety import DialogueSafety
from .ConfAIde import ConfAIde
from .ClearHarm import ClearHarm
# from .WMDP import WMDP  # excluded: unlearning / hazardous-knowledge probe, not a refusal-behaviour test
from .ORBench import ORBenchHard1K, ORBenchToxic
from .FalseReject import FalseReject
from .CoCoNot import CoCoNotOriginal, CoCoNotContrast
from .CoSafe import CoSafe
from .DiaSafety import DiaSafety
from .CASEBench import CASEBench
from .StealthGraph import StealthGraph
from .RedBenchSubsets import (
    CatQA,
    ForbiddenQuestions,
    GPTFuzzer,
    MedSafetyBench,
)
from .RealToxicityPrompts import RealToxicityPrompts
from .AyaRedTeaming import AyaRedTeaming
from .SALADBench import SALADBench
from .XSafety import XSafety
from .UAE import (
    UAESafety,
    UAETruthfulnessWiki,
    UAETruthfulnessDhow,
    UAEControversial,
)
# from .ControversialInstructions import ControversialInstructions  # 需要 OpenAI API key | requires an OpenAI API key
from .CyberattackAssistance import (
    CyberattackAssistance,
    CyberSecEval4Mitre,
)
from .PhysicalSafetyInstructions import (
    PhysicalSafetyInstructionsSafe,
    PhysicalSafetyInstructionsUnsafe,
)
#from .MaliciousInstructions import MaliciousInstructions
from .PersonalInfoLeak import (
    # PersonalInfoLeak_context, # task in completion format, not chat format
    # PersonalInfoLeak_zero_shot, # task in completion format, not chat format
    PersonalInfoLeak_few_shot, # task in completion format, but with fwe-shot, it can be valid
)
from .MoralChoice import MoralChoice
from .PromptExtractionRobustness import PromptExtractionRobustness
from .PromptHijackingRobustness import PromptHijackingRobustness
# from .QHarm import QHarm  # evaluation need double check, many questions are not risky
from .HypothesisStereotypes import HypothesisStereotypes
from .BOLD import BOLD
from .CrowSPairs import CrowSPairs
from .StereoSet import StereoSet
from .HateXplain import HateXplain
from .LatentJailbreak import LatentJailbreak
# from .JailBench import JailBench  # excluded: Chinese-only (out of English scope)
from .JailbreakBench import (
    JailbreakBench,
    JailbreakBenchBenign,
)
from .JBShield import JBShield
from .GAJailbreak import GAJailbreak
from .WildJailbreak import WildJailbreak
from .JBDistillBench import JBDistillBench
#from .MaliciousInstruct import MaliciousInstruct
# from .StrongREJECT import StrongREJECT  # sourced from other datasets
from .SycophancyEval import (
    SycophancyEvalAnswer,
    SycophancyEvalAreYouSure,
    # SycophancyEvalFeedback, # scores are all the same, need debug
    # SycophancyEvalMimicry,
)
from .TDCRedTeaming import TDCRedTeaming
from .HackAPrompt import HackAPrompt  # data need double check
#from .HarmBench import HarmBench  # 需要 torch | requires torch
from .HarmfulQ import HarmfulQ
from .DoAnythingNow import (
    DoAnythingNowJailbreak,
    DoAnythingNowRegular
)
from .GandalfIgnoreInstructions import GandalfIgnoreInstructions
#from .RedEval import (  # 需要 torch | requires torch
#    RedEvalHarmfulQA,
#    RedEvalDangerousQA,
#)
from .SafeText import SafeText
from .HExPHI import HExPHI
from .TruthfulQA import (
    TruthfulQA_mc1,
    TruthfulQA_binary,  # Jan-2025 improved binary multiple-choice setting
    # TruthfulQA_mc2,  # evaluation need revise
    # TruthfulQA_gen  # similar to mc1 task, while the evaluation seems not always correct and meaningful
)
from .XSTest import XSTest
from .Toxigen import Toxigen
from .ToxicChat import ToxicChat
from .Aart import Aart
from .SimpleSafetyTest import SimpleSafetyTest
from .SORRYBench import SORRYBench
from .SPMisconceptions import SPMisconceptions
# from .SafetyPrompt import SafetyPrompt  # Chinese
# from .AnthropicHarmlessBase import AnthropicHarmlessBase # The dataset is suitable for DPO training, but not for chat-based evaluation
from .DICES350 import DICES350
from .BBQ import BBQ
from .AnthropicRedTeam import AnthropicRedTeam
from .BAD import BAD
from .LibrAI_Adversarial import (
    # AttackCiphering, # Drop due to the difficulty of evaluation, sometimes model resopnse is ciphered and hard to judge
    AttackDeepInception,
    AttackDoAnythingNow,
    AttackEffectToCause,
    AttackFewShots,
    AttackMultilingual,
    AttackOneSidedStatement,
    AttackPersonaModulation,
    AttackPromptInjection,
    AttackRefusalSuppression,
    AttackTenseChange
)

# General evaluation
# from .MTBench import MTBench # multi-turn not implemented
from .VicunaBench import VicunaBench
# from .RuozhiBench import RuozhiBench  # excluded: Chinese-only (out of English scope)

# New tasks using GenericHarmfulTask
from .HarmBenchNew import HarmBenchNew
from .MaliciousInstructNew import MaliciousInstructNew
from .MaliciousInstructionsNew import MaliciousInstructionsNew
from .RedEvalDangerousQA import RedEvalDangerousQA
from .RedEvalHarmfulQA import RedEvalHarmfulQA
from .SycophancyEvalMimicry import SycophancyEvalMimicry

# Frontier surfaces added 2026-07: multi-turn escalation + honesty-under-pressure.
# DEREGISTERED 2026-08 for the K2-V3 family runs: V3 never ran these, so including them
# would break family comparability (the suite must stay the exact V3 report scope,
# 95 tasks). Tasks + datasets are built and judge-validated — re-enable by
# uncommenting once a full-family (V3 included) run of them is scheduled.
# from .MHJ import MHJ
# from .MASK import MASKProvidedFacts, MASKKnownFacts

try:
    from .InternalIQTest import InternalIQTest
except:
    pass

TASKS = {}
for cls_name, cls_obj in list(locals().items()):
    if isinstance(cls_obj, type) and hasattr(cls_obj, 'task_name'):
        TASKS[cls_obj.task_name] = cls_obj
