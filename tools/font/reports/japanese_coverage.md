# Japanese coverage audit

- Source: `assets/fonts/chenyuluoyan/ChenYuluoyan-2.0-Thin.ttf`
- Derived: `assets/fonts/quanfangwei-supplement/QuanFangweiSupplementScript-Regular.ttf`
- Units per em: 1024
- Source CJK Unified Ideographs coverage: 9097 code points
- Katakana Phonetic Extensions are audited only; they are not Phase 1 requirements.
- Japanese kanji entries are coverage statistics only. Shared code points continue to use the existing source glyph.

## Summary

| Category | Audited | Source present | Derived present | Phase 1 required | Phase 1 missing |
|---|---:|---:|---:|---:|---:|
| cjk_symbols_and_punctuation | 64 | 21 | 23 | 19 | 0 |
| common_japanese_kanji_sample | 21 | 21 | 21 | 0 | 0 |
| hiragana | 96 | 0 | 92 | 92 | 0 |
| katakana | 96 | 0 | 94 | 94 | 0 |
| katakana_phonetic_extensions | 16 | 0 | 0 | 0 | 0 |

## Code points

| Character | Code point | Unicode name | Source | Derived | Glyph name | Add | Category | Phase 1 |
|---|---|---|---:|---:|---|---:|---|---:|
| SPACE | U+3000 | IDEOGRAPHIC SPACE | yes | yes | uni3000 | no | cjk_symbols_and_punctuation | yes |
| 、 | U+3001 | IDEOGRAPHIC COMMA | yes | yes | uni3001 | no | cjk_symbols_and_punctuation | yes |
| 。 | U+3002 | IDEOGRAPHIC FULL STOP | yes | yes | uni3002 | no | cjk_symbols_and_punctuation | yes |
| 〃 | U+3003 | DITTO MARK | yes | yes | uni3003 | no | cjk_symbols_and_punctuation | no |
| 〄 | U+3004 | JAPANESE INDUSTRIAL STANDARD SYMBOL | no | no |  | no | cjk_symbols_and_punctuation | no |
| 々 | U+3005 | IDEOGRAPHIC ITERATION MARK | no | yes | uni3005.qfwUser | no | cjk_symbols_and_punctuation | yes |
| 〆 | U+3006 | IDEOGRAPHIC CLOSING MARK | no | yes | uni3006 | no | cjk_symbols_and_punctuation | yes |
| 〇 | U+3007 | IDEOGRAPHIC NUMBER ZERO | yes | yes | uni3007 | no | cjk_symbols_and_punctuation | yes |
| 〈 | U+3008 | LEFT ANGLE BRACKET | yes | yes | uni3008 | no | cjk_symbols_and_punctuation | yes |
| 〉 | U+3009 | RIGHT ANGLE BRACKET | yes | yes | uni3009 | no | cjk_symbols_and_punctuation | yes |
| 《 | U+300A | LEFT DOUBLE ANGLE BRACKET | yes | yes | uni300A | no | cjk_symbols_and_punctuation | yes |
| 》 | U+300B | RIGHT DOUBLE ANGLE BRACKET | yes | yes | uni300B | no | cjk_symbols_and_punctuation | yes |
| 「 | U+300C | LEFT CORNER BRACKET | yes | yes | uni300C | no | cjk_symbols_and_punctuation | yes |
| 」 | U+300D | RIGHT CORNER BRACKET | yes | yes | uni300D | no | cjk_symbols_and_punctuation | yes |
| 『 | U+300E | LEFT WHITE CORNER BRACKET | yes | yes | uni300E | no | cjk_symbols_and_punctuation | yes |
| 』 | U+300F | RIGHT WHITE CORNER BRACKET | yes | yes | uni300F | no | cjk_symbols_and_punctuation | yes |
| 【 | U+3010 | LEFT BLACK LENTICULAR BRACKET | yes | yes | uni3010 | no | cjk_symbols_and_punctuation | yes |
| 】 | U+3011 | RIGHT BLACK LENTICULAR BRACKET | yes | yes | uni3011 | no | cjk_symbols_and_punctuation | yes |
| 〒 | U+3012 | POSTAL MARK | yes | yes | uni3012 | no | cjk_symbols_and_punctuation | no |
| 〓 | U+3013 | GETA MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〔 | U+3014 | LEFT TORTOISE SHELL BRACKET | yes | yes | uni3014 | no | cjk_symbols_and_punctuation | yes |
| 〕 | U+3015 | RIGHT TORTOISE SHELL BRACKET | yes | yes | uni3015 | no | cjk_symbols_and_punctuation | yes |
| 〖 | U+3016 | LEFT WHITE LENTICULAR BRACKET | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〗 | U+3017 | RIGHT WHITE LENTICULAR BRACKET | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〘 | U+3018 | LEFT WHITE TORTOISE SHELL BRACKET | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〙 | U+3019 | RIGHT WHITE TORTOISE SHELL BRACKET | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〚 | U+301A | LEFT WHITE SQUARE BRACKET | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〛 | U+301B | RIGHT WHITE SQUARE BRACKET | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〜 | U+301C | WAVE DASH | yes | yes | uni301C | no | cjk_symbols_and_punctuation | yes |
| 〝 | U+301D | REVERSED DOUBLE PRIME QUOTATION MARK | yes | yes | uni301D | no | cjk_symbols_and_punctuation | no |
| 〞 | U+301E | DOUBLE PRIME QUOTATION MARK | yes | yes | uni301E | no | cjk_symbols_and_punctuation | no |
| 〟 | U+301F | LOW DOUBLE PRIME QUOTATION MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〠 | U+3020 | POSTAL MARK FACE | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〡 | U+3021 | HANGZHOU NUMERAL ONE | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〢 | U+3022 | HANGZHOU NUMERAL TWO | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〣 | U+3023 | HANGZHOU NUMERAL THREE | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〤 | U+3024 | HANGZHOU NUMERAL FOUR | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〥 | U+3025 | HANGZHOU NUMERAL FIVE | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〦 | U+3026 | HANGZHOU NUMERAL SIX | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〧 | U+3027 | HANGZHOU NUMERAL SEVEN | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〨 | U+3028 | HANGZHOU NUMERAL EIGHT | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〩 | U+3029 | HANGZHOU NUMERAL NINE | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〪 | U+302A | IDEOGRAPHIC LEVEL TONE MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〫 | U+302B | IDEOGRAPHIC RISING TONE MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〬 | U+302C | IDEOGRAPHIC DEPARTING TONE MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〭 | U+302D | IDEOGRAPHIC ENTERING TONE MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〮 | U+302E | HANGUL SINGLE DOT TONE MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〯 | U+302F | HANGUL DOUBLE DOT TONE MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〰 | U+3030 | WAVY DASH | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〱 | U+3031 | VERTICAL KANA REPEAT MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〲 | U+3032 | VERTICAL KANA REPEAT WITH VOICED SOUND MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〳 | U+3033 | VERTICAL KANA REPEAT MARK UPPER HALF | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〴 | U+3034 | VERTICAL KANA REPEAT WITH VOICED SOUND MARK UPPER HALF | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〵 | U+3035 | VERTICAL KANA REPEAT MARK LOWER HALF | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〶 | U+3036 | CIRCLED POSTAL MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〷 | U+3037 | IDEOGRAPHIC TELEGRAPH LINE FEED SEPARATOR SYMBOL | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〸 | U+3038 | HANGZHOU NUMERAL TEN | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〹 | U+3039 | HANGZHOU NUMERAL TWENTY | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〺 | U+303A | HANGZHOU NUMERAL THIRTY | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〻 | U+303B | VERTICAL IDEOGRAPHIC ITERATION MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〼 | U+303C | MASU MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〽 | U+303D | PART ALTERNATION MARK | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〾 | U+303E | IDEOGRAPHIC VARIATION INDICATOR | no | no |  | no | cjk_symbols_and_punctuation | no |
| 〿 | U+303F | IDEOGRAPHIC HALF FILL SPACE | no | no |  | no | cjk_symbols_and_punctuation | no |
| ぀ | U+3040 | <UNASSIGNED> | no | no |  | no | hiragana | no |
| ぁ | U+3041 | HIRAGANA LETTER SMALL A | no | yes | uni3041 | no | hiragana | yes |
| あ | U+3042 | HIRAGANA LETTER A | no | yes | uni3042 | no | hiragana | yes |
| ぃ | U+3043 | HIRAGANA LETTER SMALL I | no | yes | uni3043 | no | hiragana | yes |
| い | U+3044 | HIRAGANA LETTER I | no | yes | uni3044 | no | hiragana | yes |
| ぅ | U+3045 | HIRAGANA LETTER SMALL U | no | yes | uni3045 | no | hiragana | yes |
| う | U+3046 | HIRAGANA LETTER U | no | yes | uni3046 | no | hiragana | yes |
| ぇ | U+3047 | HIRAGANA LETTER SMALL E | no | yes | uni3047 | no | hiragana | yes |
| え | U+3048 | HIRAGANA LETTER E | no | yes | uni3048 | no | hiragana | yes |
| ぉ | U+3049 | HIRAGANA LETTER SMALL O | no | yes | uni3049 | no | hiragana | yes |
| お | U+304A | HIRAGANA LETTER O | no | yes | uni304A | no | hiragana | yes |
| か | U+304B | HIRAGANA LETTER KA | no | yes | uni304B | no | hiragana | yes |
| が | U+304C | HIRAGANA LETTER GA | no | yes | uni304C | no | hiragana | yes |
| き | U+304D | HIRAGANA LETTER KI | no | yes | uni304D | no | hiragana | yes |
| ぎ | U+304E | HIRAGANA LETTER GI | no | yes | uni304E | no | hiragana | yes |
| く | U+304F | HIRAGANA LETTER KU | no | yes | uni304F | no | hiragana | yes |
| ぐ | U+3050 | HIRAGANA LETTER GU | no | yes | uni3050 | no | hiragana | yes |
| け | U+3051 | HIRAGANA LETTER KE | no | yes | uni3051 | no | hiragana | yes |
| げ | U+3052 | HIRAGANA LETTER GE | no | yes | uni3052 | no | hiragana | yes |
| こ | U+3053 | HIRAGANA LETTER KO | no | yes | uni3053 | no | hiragana | yes |
| ご | U+3054 | HIRAGANA LETTER GO | no | yes | uni3054 | no | hiragana | yes |
| さ | U+3055 | HIRAGANA LETTER SA | no | yes | uni3055 | no | hiragana | yes |
| ざ | U+3056 | HIRAGANA LETTER ZA | no | yes | uni3056 | no | hiragana | yes |
| し | U+3057 | HIRAGANA LETTER SI | no | yes | uni3057 | no | hiragana | yes |
| じ | U+3058 | HIRAGANA LETTER ZI | no | yes | uni3058 | no | hiragana | yes |
| す | U+3059 | HIRAGANA LETTER SU | no | yes | uni3059 | no | hiragana | yes |
| ず | U+305A | HIRAGANA LETTER ZU | no | yes | uni305A | no | hiragana | yes |
| せ | U+305B | HIRAGANA LETTER SE | no | yes | uni305B | no | hiragana | yes |
| ぜ | U+305C | HIRAGANA LETTER ZE | no | yes | uni305C | no | hiragana | yes |
| そ | U+305D | HIRAGANA LETTER SO | no | yes | uni305D | no | hiragana | yes |
| ぞ | U+305E | HIRAGANA LETTER ZO | no | yes | uni305E | no | hiragana | yes |
| た | U+305F | HIRAGANA LETTER TA | no | yes | uni305F | no | hiragana | yes |
| だ | U+3060 | HIRAGANA LETTER DA | no | yes | uni3060 | no | hiragana | yes |
| ち | U+3061 | HIRAGANA LETTER TI | no | yes | uni3061 | no | hiragana | yes |
| ぢ | U+3062 | HIRAGANA LETTER DI | no | yes | uni3062 | no | hiragana | yes |
| っ | U+3063 | HIRAGANA LETTER SMALL TU | no | yes | uni3063 | no | hiragana | yes |
| つ | U+3064 | HIRAGANA LETTER TU | no | yes | uni3064 | no | hiragana | yes |
| づ | U+3065 | HIRAGANA LETTER DU | no | yes | uni3065 | no | hiragana | yes |
| て | U+3066 | HIRAGANA LETTER TE | no | yes | uni3066 | no | hiragana | yes |
| で | U+3067 | HIRAGANA LETTER DE | no | yes | uni3067 | no | hiragana | yes |
| と | U+3068 | HIRAGANA LETTER TO | no | yes | uni3068 | no | hiragana | yes |
| ど | U+3069 | HIRAGANA LETTER DO | no | yes | uni3069 | no | hiragana | yes |
| な | U+306A | HIRAGANA LETTER NA | no | yes | uni306A | no | hiragana | yes |
| に | U+306B | HIRAGANA LETTER NI | no | yes | uni306B | no | hiragana | yes |
| ぬ | U+306C | HIRAGANA LETTER NU | no | yes | uni306C | no | hiragana | yes |
| ね | U+306D | HIRAGANA LETTER NE | no | yes | uni306D | no | hiragana | yes |
| の | U+306E | HIRAGANA LETTER NO | no | yes | uni306E | no | hiragana | yes |
| は | U+306F | HIRAGANA LETTER HA | no | yes | uni306F | no | hiragana | yes |
| ば | U+3070 | HIRAGANA LETTER BA | no | yes | uni3070 | no | hiragana | yes |
| ぱ | U+3071 | HIRAGANA LETTER PA | no | yes | uni3071 | no | hiragana | yes |
| ひ | U+3072 | HIRAGANA LETTER HI | no | yes | uni3072 | no | hiragana | yes |
| び | U+3073 | HIRAGANA LETTER BI | no | yes | uni3073 | no | hiragana | yes |
| ぴ | U+3074 | HIRAGANA LETTER PI | no | yes | uni3074 | no | hiragana | yes |
| ふ | U+3075 | HIRAGANA LETTER HU | no | yes | uni3075 | no | hiragana | yes |
| ぶ | U+3076 | HIRAGANA LETTER BU | no | yes | uni3076 | no | hiragana | yes |
| ぷ | U+3077 | HIRAGANA LETTER PU | no | yes | uni3077 | no | hiragana | yes |
| へ | U+3078 | HIRAGANA LETTER HE | no | yes | uni3078 | no | hiragana | yes |
| べ | U+3079 | HIRAGANA LETTER BE | no | yes | uni3079 | no | hiragana | yes |
| ぺ | U+307A | HIRAGANA LETTER PE | no | yes | uni307A | no | hiragana | yes |
| ほ | U+307B | HIRAGANA LETTER HO | no | yes | uni307B | no | hiragana | yes |
| ぼ | U+307C | HIRAGANA LETTER BO | no | yes | uni307C | no | hiragana | yes |
| ぽ | U+307D | HIRAGANA LETTER PO | no | yes | uni307D | no | hiragana | yes |
| ま | U+307E | HIRAGANA LETTER MA | no | yes | uni307E | no | hiragana | yes |
| み | U+307F | HIRAGANA LETTER MI | no | yes | uni307F | no | hiragana | yes |
| む | U+3080 | HIRAGANA LETTER MU | no | yes | uni3080 | no | hiragana | yes |
| め | U+3081 | HIRAGANA LETTER ME | no | yes | uni3081 | no | hiragana | yes |
| も | U+3082 | HIRAGANA LETTER MO | no | yes | uni3082 | no | hiragana | yes |
| ゃ | U+3083 | HIRAGANA LETTER SMALL YA | no | yes | uni3083 | no | hiragana | yes |
| や | U+3084 | HIRAGANA LETTER YA | no | yes | uni3084 | no | hiragana | yes |
| ゅ | U+3085 | HIRAGANA LETTER SMALL YU | no | yes | uni3085 | no | hiragana | yes |
| ゆ | U+3086 | HIRAGANA LETTER YU | no | yes | uni3086 | no | hiragana | yes |
| ょ | U+3087 | HIRAGANA LETTER SMALL YO | no | yes | uni3087 | no | hiragana | yes |
| よ | U+3088 | HIRAGANA LETTER YO | no | yes | uni3088 | no | hiragana | yes |
| ら | U+3089 | HIRAGANA LETTER RA | no | yes | uni3089 | no | hiragana | yes |
| り | U+308A | HIRAGANA LETTER RI | no | yes | uni308A | no | hiragana | yes |
| る | U+308B | HIRAGANA LETTER RU | no | yes | uni308B | no | hiragana | yes |
| れ | U+308C | HIRAGANA LETTER RE | no | yes | uni308C | no | hiragana | yes |
| ろ | U+308D | HIRAGANA LETTER RO | no | yes | uni308D | no | hiragana | yes |
| ゎ | U+308E | HIRAGANA LETTER SMALL WA | no | yes | uni308E | no | hiragana | yes |
| わ | U+308F | HIRAGANA LETTER WA | no | yes | uni308F | no | hiragana | yes |
| ゐ | U+3090 | HIRAGANA LETTER WI | no | yes | uni3090 | no | hiragana | yes |
| ゑ | U+3091 | HIRAGANA LETTER WE | no | yes | uni3091 | no | hiragana | yes |
| を | U+3092 | HIRAGANA LETTER WO | no | yes | uni3092 | no | hiragana | yes |
| ん | U+3093 | HIRAGANA LETTER N | no | yes | uni3093 | no | hiragana | yes |
| ゔ | U+3094 | HIRAGANA LETTER VU | no | yes | uni3094 | no | hiragana | yes |
| ゕ | U+3095 | HIRAGANA LETTER SMALL KA | no | yes | uni3095 | no | hiragana | yes |
| ゖ | U+3096 | HIRAGANA LETTER SMALL KE | no | yes | uni3096 | no | hiragana | yes |
| ゗ | U+3097 | <UNASSIGNED> | no | no |  | no | hiragana | no |
| ゘ | U+3098 | <UNASSIGNED> | no | no |  | no | hiragana | no |
| ゙ | U+3099 | COMBINING KATAKANA-HIRAGANA VOICED SOUND MARK | no | yes | uni3099 | no | hiragana | yes |
| ゚ | U+309A | COMBINING KATAKANA-HIRAGANA SEMI-VOICED SOUND MARK | no | yes | uni309A | no | hiragana | yes |
| ゛ | U+309B | KATAKANA-HIRAGANA VOICED SOUND MARK | no | yes | uni309B | no | hiragana | yes |
| ゜ | U+309C | KATAKANA-HIRAGANA SEMI-VOICED SOUND MARK | no | yes | uni309C | no | hiragana | yes |
| ゝ | U+309D | HIRAGANA ITERATION MARK | no | yes | uni309D | no | hiragana | yes |
| ゞ | U+309E | HIRAGANA VOICED ITERATION MARK | no | yes | uni309E | no | hiragana | yes |
| ゟ | U+309F | HIRAGANA DIGRAPH YORI | no | no |  | no | hiragana | no |
| ゠ | U+30A0 | KATAKANA-HIRAGANA DOUBLE HYPHEN | no | no |  | no | katakana | no |
| ァ | U+30A1 | KATAKANA LETTER SMALL A | no | yes | uni30A1 | no | katakana | yes |
| ア | U+30A2 | KATAKANA LETTER A | no | yes | uni30A2 | no | katakana | yes |
| ィ | U+30A3 | KATAKANA LETTER SMALL I | no | yes | uni30A3 | no | katakana | yes |
| イ | U+30A4 | KATAKANA LETTER I | no | yes | uni30A4 | no | katakana | yes |
| ゥ | U+30A5 | KATAKANA LETTER SMALL U | no | yes | uni30A5 | no | katakana | yes |
| ウ | U+30A6 | KATAKANA LETTER U | no | yes | uni30A6 | no | katakana | yes |
| ェ | U+30A7 | KATAKANA LETTER SMALL E | no | yes | uni30A7 | no | katakana | yes |
| エ | U+30A8 | KATAKANA LETTER E | no | yes | uni30A8 | no | katakana | yes |
| ォ | U+30A9 | KATAKANA LETTER SMALL O | no | yes | uni30A9 | no | katakana | yes |
| オ | U+30AA | KATAKANA LETTER O | no | yes | uni30AA | no | katakana | yes |
| カ | U+30AB | KATAKANA LETTER KA | no | yes | uni30AB | no | katakana | yes |
| ガ | U+30AC | KATAKANA LETTER GA | no | yes | uni30AC | no | katakana | yes |
| キ | U+30AD | KATAKANA LETTER KI | no | yes | uni30AD | no | katakana | yes |
| ギ | U+30AE | KATAKANA LETTER GI | no | yes | uni30AE | no | katakana | yes |
| ク | U+30AF | KATAKANA LETTER KU | no | yes | uni30AF | no | katakana | yes |
| グ | U+30B0 | KATAKANA LETTER GU | no | yes | uni30B0 | no | katakana | yes |
| ケ | U+30B1 | KATAKANA LETTER KE | no | yes | uni30B1 | no | katakana | yes |
| ゲ | U+30B2 | KATAKANA LETTER GE | no | yes | uni30B2 | no | katakana | yes |
| コ | U+30B3 | KATAKANA LETTER KO | no | yes | uni30B3 | no | katakana | yes |
| ゴ | U+30B4 | KATAKANA LETTER GO | no | yes | uni30B4 | no | katakana | yes |
| サ | U+30B5 | KATAKANA LETTER SA | no | yes | uni30B5 | no | katakana | yes |
| ザ | U+30B6 | KATAKANA LETTER ZA | no | yes | uni30B6 | no | katakana | yes |
| シ | U+30B7 | KATAKANA LETTER SI | no | yes | uni30B7 | no | katakana | yes |
| ジ | U+30B8 | KATAKANA LETTER ZI | no | yes | uni30B8 | no | katakana | yes |
| ス | U+30B9 | KATAKANA LETTER SU | no | yes | uni30B9 | no | katakana | yes |
| ズ | U+30BA | KATAKANA LETTER ZU | no | yes | uni30BA | no | katakana | yes |
| セ | U+30BB | KATAKANA LETTER SE | no | yes | uni30BB | no | katakana | yes |
| ゼ | U+30BC | KATAKANA LETTER ZE | no | yes | uni30BC | no | katakana | yes |
| ソ | U+30BD | KATAKANA LETTER SO | no | yes | uni30BD | no | katakana | yes |
| ゾ | U+30BE | KATAKANA LETTER ZO | no | yes | uni30BE | no | katakana | yes |
| タ | U+30BF | KATAKANA LETTER TA | no | yes | uni30BF | no | katakana | yes |
| ダ | U+30C0 | KATAKANA LETTER DA | no | yes | uni30C0 | no | katakana | yes |
| チ | U+30C1 | KATAKANA LETTER TI | no | yes | uni30C1 | no | katakana | yes |
| ヂ | U+30C2 | KATAKANA LETTER DI | no | yes | uni30C2 | no | katakana | yes |
| ッ | U+30C3 | KATAKANA LETTER SMALL TU | no | yes | uni30C3 | no | katakana | yes |
| ツ | U+30C4 | KATAKANA LETTER TU | no | yes | uni30C4 | no | katakana | yes |
| ヅ | U+30C5 | KATAKANA LETTER DU | no | yes | uni30C5 | no | katakana | yes |
| テ | U+30C6 | KATAKANA LETTER TE | no | yes | uni30C6 | no | katakana | yes |
| デ | U+30C7 | KATAKANA LETTER DE | no | yes | uni30C7 | no | katakana | yes |
| ト | U+30C8 | KATAKANA LETTER TO | no | yes | uni30C8 | no | katakana | yes |
| ド | U+30C9 | KATAKANA LETTER DO | no | yes | uni30C9 | no | katakana | yes |
| ナ | U+30CA | KATAKANA LETTER NA | no | yes | uni30CA | no | katakana | yes |
| ニ | U+30CB | KATAKANA LETTER NI | no | yes | uni30CB | no | katakana | yes |
| ヌ | U+30CC | KATAKANA LETTER NU | no | yes | uni30CC | no | katakana | yes |
| ネ | U+30CD | KATAKANA LETTER NE | no | yes | uni30CD | no | katakana | yes |
| ノ | U+30CE | KATAKANA LETTER NO | no | yes | uni30CE | no | katakana | yes |
| ハ | U+30CF | KATAKANA LETTER HA | no | yes | uni30CF | no | katakana | yes |
| バ | U+30D0 | KATAKANA LETTER BA | no | yes | uni30D0 | no | katakana | yes |
| パ | U+30D1 | KATAKANA LETTER PA | no | yes | uni30D1 | no | katakana | yes |
| ヒ | U+30D2 | KATAKANA LETTER HI | no | yes | uni30D2 | no | katakana | yes |
| ビ | U+30D3 | KATAKANA LETTER BI | no | yes | uni30D3 | no | katakana | yes |
| ピ | U+30D4 | KATAKANA LETTER PI | no | yes | uni30D4 | no | katakana | yes |
| フ | U+30D5 | KATAKANA LETTER HU | no | yes | uni30D5 | no | katakana | yes |
| ブ | U+30D6 | KATAKANA LETTER BU | no | yes | uni30D6 | no | katakana | yes |
| プ | U+30D7 | KATAKANA LETTER PU | no | yes | uni30D7 | no | katakana | yes |
| ヘ | U+30D8 | KATAKANA LETTER HE | no | yes | uni30D8 | no | katakana | yes |
| ベ | U+30D9 | KATAKANA LETTER BE | no | yes | uni30D9 | no | katakana | yes |
| ペ | U+30DA | KATAKANA LETTER PE | no | yes | uni30DA | no | katakana | yes |
| ホ | U+30DB | KATAKANA LETTER HO | no | yes | uni30DB | no | katakana | yes |
| ボ | U+30DC | KATAKANA LETTER BO | no | yes | uni30DC | no | katakana | yes |
| ポ | U+30DD | KATAKANA LETTER PO | no | yes | uni30DD | no | katakana | yes |
| マ | U+30DE | KATAKANA LETTER MA | no | yes | uni30DE | no | katakana | yes |
| ミ | U+30DF | KATAKANA LETTER MI | no | yes | uni30DF | no | katakana | yes |
| ム | U+30E0 | KATAKANA LETTER MU | no | yes | uni30E0 | no | katakana | yes |
| メ | U+30E1 | KATAKANA LETTER ME | no | yes | uni30E1 | no | katakana | yes |
| モ | U+30E2 | KATAKANA LETTER MO | no | yes | uni30E2 | no | katakana | yes |
| ャ | U+30E3 | KATAKANA LETTER SMALL YA | no | yes | uni30E3 | no | katakana | yes |
| ヤ | U+30E4 | KATAKANA LETTER YA | no | yes | uni30E4 | no | katakana | yes |
| ュ | U+30E5 | KATAKANA LETTER SMALL YU | no | yes | uni30E5 | no | katakana | yes |
| ユ | U+30E6 | KATAKANA LETTER YU | no | yes | uni30E6 | no | katakana | yes |
| ョ | U+30E7 | KATAKANA LETTER SMALL YO | no | yes | uni30E7 | no | katakana | yes |
| ヨ | U+30E8 | KATAKANA LETTER YO | no | yes | uni30E8 | no | katakana | yes |
| ラ | U+30E9 | KATAKANA LETTER RA | no | yes | uni30E9 | no | katakana | yes |
| リ | U+30EA | KATAKANA LETTER RI | no | yes | uni30EA | no | katakana | yes |
| ル | U+30EB | KATAKANA LETTER RU | no | yes | uni30EB | no | katakana | yes |
| レ | U+30EC | KATAKANA LETTER RE | no | yes | uni30EC | no | katakana | yes |
| ロ | U+30ED | KATAKANA LETTER RO | no | yes | uni30ED | no | katakana | yes |
| ヮ | U+30EE | KATAKANA LETTER SMALL WA | no | yes | uni30EE | no | katakana | yes |
| ワ | U+30EF | KATAKANA LETTER WA | no | yes | uni30EF | no | katakana | yes |
| ヰ | U+30F0 | KATAKANA LETTER WI | no | yes | uni30F0 | no | katakana | yes |
| ヱ | U+30F1 | KATAKANA LETTER WE | no | yes | uni30F1 | no | katakana | yes |
| ヲ | U+30F2 | KATAKANA LETTER WO | no | yes | uni30F2 | no | katakana | yes |
| ン | U+30F3 | KATAKANA LETTER N | no | yes | uni30F3 | no | katakana | yes |
| ヴ | U+30F4 | KATAKANA LETTER VU | no | yes | uni30F4 | no | katakana | yes |
| ヵ | U+30F5 | KATAKANA LETTER SMALL KA | no | yes | uni30F5 | no | katakana | yes |
| ヶ | U+30F6 | KATAKANA LETTER SMALL KE | no | yes | uni30F6 | no | katakana | yes |
| ヷ | U+30F7 | KATAKANA LETTER VA | no | yes | uni30F7 | no | katakana | yes |
| ヸ | U+30F8 | KATAKANA LETTER VI | no | yes | uni30F8 | no | katakana | yes |
| ヹ | U+30F9 | KATAKANA LETTER VE | no | yes | uni30F9 | no | katakana | yes |
| ヺ | U+30FA | KATAKANA LETTER VO | no | yes | uni30FA | no | katakana | yes |
| ・ | U+30FB | KATAKANA MIDDLE DOT | no | yes | uni30FB | no | katakana | yes |
| ー | U+30FC | KATAKANA-HIRAGANA PROLONGED SOUND MARK | no | yes | uni30FC | no | katakana | yes |
| ヽ | U+30FD | KATAKANA ITERATION MARK | no | yes | uni30FD | no | katakana | yes |
| ヾ | U+30FE | KATAKANA VOICED ITERATION MARK | no | yes | uni30FE | no | katakana | yes |
| ヿ | U+30FF | KATAKANA DIGRAPH KOTO | no | no |  | no | katakana | no |
| ㇰ | U+31F0 | KATAKANA LETTER SMALL KU | no | no |  | no | katakana_phonetic_extensions | no |
| ㇱ | U+31F1 | KATAKANA LETTER SMALL SI | no | no |  | no | katakana_phonetic_extensions | no |
| ㇲ | U+31F2 | KATAKANA LETTER SMALL SU | no | no |  | no | katakana_phonetic_extensions | no |
| ㇳ | U+31F3 | KATAKANA LETTER SMALL TO | no | no |  | no | katakana_phonetic_extensions | no |
| ㇴ | U+31F4 | KATAKANA LETTER SMALL NU | no | no |  | no | katakana_phonetic_extensions | no |
| ㇵ | U+31F5 | KATAKANA LETTER SMALL HA | no | no |  | no | katakana_phonetic_extensions | no |
| ㇶ | U+31F6 | KATAKANA LETTER SMALL HI | no | no |  | no | katakana_phonetic_extensions | no |
| ㇷ | U+31F7 | KATAKANA LETTER SMALL HU | no | no |  | no | katakana_phonetic_extensions | no |
| ㇸ | U+31F8 | KATAKANA LETTER SMALL HE | no | no |  | no | katakana_phonetic_extensions | no |
| ㇹ | U+31F9 | KATAKANA LETTER SMALL HO | no | no |  | no | katakana_phonetic_extensions | no |
| ㇺ | U+31FA | KATAKANA LETTER SMALL MU | no | no |  | no | katakana_phonetic_extensions | no |
| ㇻ | U+31FB | KATAKANA LETTER SMALL RA | no | no |  | no | katakana_phonetic_extensions | no |
| ㇼ | U+31FC | KATAKANA LETTER SMALL RI | no | no |  | no | katakana_phonetic_extensions | no |
| ㇽ | U+31FD | KATAKANA LETTER SMALL RU | no | no |  | no | katakana_phonetic_extensions | no |
| ㇾ | U+31FE | KATAKANA LETTER SMALL RE | no | no |  | no | katakana_phonetic_extensions | no |
| ㇿ | U+31FF | KATAKANA LETTER SMALL RO | no | no |  | no | katakana_phonetic_extensions | no |
| 一 | U+4E00 | CJK UNIFIED IDEOGRAPH-4E00 | yes | yes | uni4E00 | no | common_japanese_kanji_sample | no |
| 上 | U+4E0A | CJK UNIFIED IDEOGRAPH-4E0A | yes | yes | uni4E0A | no | common_japanese_kanji_sample | no |
| 中 | U+4E2D | CJK UNIFIED IDEOGRAPH-4E2D | yes | yes | uni4E2D | no | common_japanese_kanji_sample | no |
| 会 | U+4F1A | CJK UNIFIED IDEOGRAPH-4F1A | yes | yes | uni4F1A | no | common_japanese_kanji_sample | no |
| 君 | U+541B | CJK UNIFIED IDEOGRAPH-541B | yes | yes | uni541B | no | common_japanese_kanji_sample | no |
| 吹 | U+5439 | CJK UNIFIED IDEOGRAPH-5439 | yes | yes | uni5439 | no | common_japanese_kanji_sample | no |
| 声 | U+58F0 | CJK UNIFIED IDEOGRAPH-58F0 | yes | yes | uni58F0 | no | common_japanese_kanji_sample | no |
| 夜 | U+591C | CJK UNIFIED IDEOGRAPH-591C | yes | yes | uni591C | no | common_japanese_kanji_sample | no |
| 夢 | U+5922 | CJK UNIFIED IDEOGRAPH-5922 | yes | yes | uni5922 | no | common_japanese_kanji_sample | no |
| 度 | U+5EA6 | CJK UNIFIED IDEOGRAPH-5EA6 | yes | yes | uni5EA6 | no | common_japanese_kanji_sample | no |
| 心 | U+5FC3 | CJK UNIFIED IDEOGRAPH-5FC3 | yes | yes | uni5FC3 | no | common_japanese_kanji_sample | no |
| 愛 | U+611B | CJK UNIFIED IDEOGRAPH-611B | yes | yes | uni611B | no | common_japanese_kanji_sample | no |
| 日 | U+65E5 | CJK UNIFIED IDEOGRAPH-65E5 | yes | yes | uni65E5 | no | common_japanese_kanji_sample | no |
| 明 | U+660E | CJK UNIFIED IDEOGRAPH-660E | yes | yes | uni660E | no | common_japanese_kanji_sample | no |
| 春 | U+6625 | CJK UNIFIED IDEOGRAPH-6625 | yes | yes | uni6625 | no | common_japanese_kanji_sample | no |
| 晴 | U+6674 | CJK UNIFIED IDEOGRAPH-6674 | yes | yes | uni6674 | no | common_japanese_kanji_sample | no |
| 空 | U+7A7A | CJK UNIFIED IDEOGRAPH-7A7A | yes | yes | uni7A7A | no | common_japanese_kanji_sample | no |
| 聞 | U+805E | CJK UNIFIED IDEOGRAPH-805E | yes | yes | uni805E | no | common_japanese_kanji_sample | no |
| 見 | U+898B | CJK UNIFIED IDEOGRAPH-898B | yes | yes | uni898B | no | common_japanese_kanji_sample | no |
| 言 | U+8A00 | CJK UNIFIED IDEOGRAPH-8A00 | yes | yes | uni8A00 | no | common_japanese_kanji_sample | no |
| 風 | U+98A8 | CJK UNIFIED IDEOGRAPH-98A8 | yes | yes | uni98A8 | no | common_japanese_kanji_sample | no |
