# Audiobook Acceptance Corpus

> Purpose: define fixed text sets for evaluating the audiobook converter through the web app.
> Rule: these texts are the canonical acceptance inputs. Do not silently replace them with shorter samples, synthetic filler, or demo-only content.

## Usage

Use these texts only for end-to-end evaluation of the current app.

Required execution rules:
- Upload the text through the web UI or `POST /api/jobs`.
- Use a real GPT-SoVITS endpoint when evaluating product readiness.
- If a demo or mock endpoint is used, mark the run as `infrastructure-only`, not product acceptance.
- Keep the corpus text unchanged unless the evaluation spec itself is revised.

## Corpus A: Narration + Dialogue + Two-Cast Suspense

Goal:
- Verify narration vs character separation.
- Verify at least two distinct speaking roles.
- Verify emotion transitions in dialogue.

Text:

```text
第一章 雨夜来电

凌晨一点，旧城区的雨还没有停。路灯把积水照得发白，巷口的便利店只剩一扇门半开着。林秋把湿透的伞靠在墙边，盯着手机上陌生号码闪烁。电话铃响了第三次，她才按下接听。

“你终于接电话了。”男人的声音压得很低，像是在压住呼吸，“别回家，立刻去南平码头。”

林秋皱起眉，语气克制：“你是谁？”

对方沉默了两秒，随后一字一顿地说：“如果你还想见到陈渡，就按我说的做。”

雨点敲在铁皮棚上，像一阵凌乱的鼓声。林秋心里一沉。陈渡是她的搭档，也是报社里唯一知道她在追那桩旧案的人。三个小时前，陈渡还发消息说采访结束后会回社里整理录音。那条消息停在晚上九点十七分，此后再没有回复。

“你在骗我。”林秋压住慌乱，尽量让声音听上去平静，“陈渡不会无缘无故失联。”

男人冷笑了一声：“你当然可以不信。二十分钟后，码头七号仓库的门会开一次。来不来，由你决定。”

通话戛然而止。

林秋站在原地，呼吸一时发空。她知道这很可能是个陷阱，可如果陈渡真的在那里，她没有第二个选择。她快步走出便利店，拦下一辆出租车。

司机是个四十多岁的男人，透过后视镜打量了她一眼：“姑娘，这么晚还往江边去？”

“南平码头。”林秋把门一关，语速很快，“麻烦快一点。”

“那地方夜里偏得很。”司机摇摇头，“前两天还停过警车。你确定要去？”

“确定。”

车轮碾过水坑，溅起一片脏白的水花。林秋靠在后座，手心全是汗。她努力回想陈渡最后一次发语音时的语气，那时候他还在笑，说这次的线索如果坐实，他们也许能把十年前那场仓库火灾重新翻出来。

十年前，她父亲死在那场火灾里。所有人都说是意外，只有她始终不信。
```

Evaluation intent:
- Narration should stay stable and restrained.
- The caller, Lin Qiu, and the driver should be distinguishable.
- The emotional turn from calm to panic to determination should be audible.

## Corpus B: Three-Character Confrontation

Goal:
- Verify multi-character differentiation.
- Verify consistent voice assignment across repeated mentions.
- Verify dialogue turns do not collapse into one voice.

Text:

```text
第二章 旧仓库

二十分钟后，出租车停在码头外的铁门边。江风带着湿冷的咸味，吹得人骨头都发涩。林秋推门下车，远处废弃仓库群像一排沉默的黑影，只有七号仓库上方的一盏旧灯忽明忽暗。

“我在这儿等你十分钟。”司机说，“要是你不出来，我可就走了。”

林秋点点头：“谢谢。”

她沿着积水的路往前走，高跟鞋在水泥地上敲出清晰的声音。越靠近七号仓库，她心里那股不祥的预感越重。门半掩着，里面透出一线冷白色的灯光。

她推门进去，看见陈渡坐在椅子上，双手被绑在身后，额角有一道明显的擦伤。

“陈渡！”林秋失声喊出来，声音第一次带上明显的惊慌。

陈渡猛地抬头：“你怎么来了？我不是让你别管吗！”

“你让我别管？”林秋几乎气笑了，“你人都被绑在这里了，我还能当作什么都没发生？”

角落里传来缓慢的掌声。

一个穿黑色长风衣的男人从阴影里走出来，眉眼瘦削，神情却从容得可怕。林秋认出他的一瞬间，后背一下子绷紧了。

“周敬川。”她咬着牙，“果然是你。”

周敬川微微一笑：“十年不见，你比我想象中更像你父亲。”

“你没资格提他！”林秋声音陡然拔高，“如果不是你，当年那场火根本不会烧起来！”

陈渡急得声音都哑了：“林秋，别跟他硬来，他就是故意激你！”

周敬川慢条斯理地走近两步：“记者讲证据，不讲情绪。”
```

Evaluation intent:
- Three voices must remain distinct.
- Speaker changes must be obvious and consistent.
- Aggressive, urgent, and controlled tones should differ.

## Corpus C: Emotion Shift Monologue

Goal:
- Verify one character can move through multiple emotional states.
- Verify emotion rendering is not flattened to one tone.

Text:

```text
第三章 录音笔

周敬川把一支旧录音笔放在铁桌上，边缘磨损得厉害，像被人反复握过很多次。陈渡盯着那支录音笔，呼吸一滞。

“这是我今晚找到的那支……”他低声说。

林秋看着他：“里面是什么？”

周敬川低头按下播放键：“你父亲留下的最后一段录音。你不是一直想知道，他临死前到底看见了什么吗？”

电流声先响了几秒，紧接着，一个嘶哑而急促的男声从录音笔里传出来。

“仓库不是意外起火……有人提前换了线路……如果我没出去，告诉小秋，不要信周——”

录音在这里中断，只剩一片刺耳的沙沙声。

仓库里安静得吓人。

林秋站着没动，手指却控制不住地发抖。她等了十年，第一次离那个答案这样近，可真正听见父亲声音的时候，心口反而像被什么东西狠狠掏空了。那种迟来的悲伤穿过她胸口，慢慢沉到最深处，几乎让人喘不过气。

“你现在听见了。”周敬川低声说，“可惜他没来得及说完。”

林秋抬起头，眼里已经没有先前的慌乱，只剩下一种压得极深的冷意：“后半句我知道。他想说的是，不要信你。”

周敬川盯着她，神情第一次真正阴沉下来。
```

Evaluation intent:
- The same character should sound restrained, then shaken, then cold and decisive.
- Emotional modulation should be audible in critical sentences, not just metadata.

## Corpus D: Pure Narration Stress Test

Goal:
- Verify the system handles no-dialogue prose honestly.
- Verify narration tone stays natural without inventing speakers.

Text:

```text
第四章 清晨

天快亮的时候，雨终于停了。城市像刚从水里捞出来一样，玻璃窗上挂着细密的水痕，街道上偶尔有早班公交车缓慢驶过。林秋站在窗边，看着天色从灰白变成淡蓝，手里的录音笔已经被她握得发热。

她没有马上去听第二遍。

十年的追问像一条看不见的线，把她一路拉到今天。她曾经以为真相只会带来答案，后来才慢慢明白，真相也会带来责任，带来失去，带来必须继续往前走的理由。

楼下传来早餐摊开火的声音，油锅里冒出轻微的爆裂声。远处有人在按喇叭，声音被晨雾削得很薄。林秋把录音笔放进外套口袋，转身离开窗边。

门开合的一瞬间，清晨的风吹了进来。她知道，接下来要面对的不只是一个人，也不是一桩旧案，而是她父亲留下的整个真相。
```

Evaluation intent:
- Narration-only sections must not be misclassified as dialogue.
- The narrator voice should remain stable and not become theatrical.

## Corpus selection rules

- Run Corpus A as the default smoke acceptance input.
- Run Corpus B and C for any claim about character separation or emotion.
- Run Corpus D whenever narration handling changes.
- If the implementation uses a placeholder endpoint, the corpus can only support infrastructure tests, not product acceptance.
- Record the exact corpus ID in the job report or test notes.
