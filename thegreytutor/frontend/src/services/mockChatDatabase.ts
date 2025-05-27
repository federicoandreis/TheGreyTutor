// src/services/mockChatDatabase.ts
// A simple mock database for chat answers for testing purposes

export interface MockChatQA {
  keywords: RegExp;
  answer: string;
}

export const mockChatAnswers: MockChatQA[] = [
  {
    keywords: /minas tirith|white city|gondor capital/i,
    answer: 'Minas Tirith, also known as the White City, is the capital of Gondor and a key location in the War of the Ring.'
  },
  {
    keywords: /eowyn|shieldmaiden|witch-king/i,
    answer: 'Éowyn is a noblewoman of Rohan, famed for slaying the Witch-king of Angmar during the Battle of the Pelennor Fields.'
  },
  {
    keywords: /witch-king|angmar|lord of the nazgûl/i,
    answer: 'The Witch-king of Angmar is the leader of the Nazgûl, Sauron’s most feared servants.'
  },
  {
    keywords: /treebeard|ents|fangorn/i,
    answer: 'Treebeard is the eldest of the Ents, ancient tree-like beings who dwell in Fangorn Forest and play a role in the downfall of Isengard.'
  },
  {
    keywords: /gimli|dwarf|dwarves|erebor|gloin/i,
    answer: 'Gimli is a dwarf warrior, son of Glóin, and a member of the Fellowship. Dwarves are skilled craftsmen and miners, with Erebor (the Lonely Mountain) as one of their great realms.'
  },
  {
    keywords: /tom bombadil|goldberry/i,
    answer: 'Tom Bombadil is a mysterious, powerful being who lives in the Old Forest with his wife Goldberry. His true nature is unknown, and he is unaffected by the power of the One Ring.'
  },
  {
    keywords: /barrow-wights|barrow downs/i,
    answer: 'Barrow-wights are evil spirits inhabiting the Barrow-downs near the Shire, known for capturing the hobbits in The Fellowship of the Ring.'
  },
  {
    keywords: /glorfindel/i,
    answer: 'Glorfindel is a mighty Elf-lord of Rivendell who helps Frodo reach safety. He is renowned for his valor and wisdom.'
  },
  {
    keywords: /grey havens|elves depart|cirdan/i,
    answer: 'The Grey Havens is a harbor in the west of Middle Earth from which Elves depart to Valinor. Círdan the Shipwright is its guardian.'
  },
  {
    keywords: /palantir|seeing-stone/i,
    answer: 'The Palantíri are ancient seeing-stones used for communication and vision across great distances. Saruman and Sauron both use them.'
  },
  {
    keywords: /uruk-hai|isengard army|lurtz/i,
    answer: 'The Uruk-hai are a breed of orcs created by Saruman to serve as his army. Lurtz is their notable leader in the films.'
  },
  {
    keywords: /black gate|morannon/i,
    answer: 'The Black Gate, or Morannon, is the main entrance to Mordor, heavily fortified and guarded.'
  },
  {
    keywords: /dead marshes|ghosts|battle of dagorlad/i,
    answer: 'The Dead Marshes are haunted wetlands filled with the spirits of those who died in the Battle of Dagorlad, near the borders of Mordor.'
  },
  {
    keywords: /helms deep|hornburg|rohan fortress/i,
    answer: 'Helm’s Deep, with its fortress the Hornburg, is a stronghold of Rohan and the site of a great battle against Saruman’s forces.'
  },
  {
    keywords: /mountain trolls|cave troll|trolls/i,
    answer: 'Trolls are large, fearsome creatures used as shock troops by Sauron and other dark powers. The Fellowship faces a cave troll in Moria.'
  },
  {
    keywords: /arda|ainur|valar|maiar/i,
    answer: 'Arda is the world in Tolkien’s legendarium. The Ainur are divine spirits, divided into the Valar (greater powers) and Maiar (lesser spirits, including Gandalf and Sauron).'
  },
  {
    keywords: /gandalf|wizard|grey/i,
    answer: 'Gandalf is a wise wizard and a member of the Istari, known for guiding the Fellowship of the Ring in their quest against Sauron.'
  },
  {
    keywords: /one ring|the ring|ring of power|sauron.*ring/i,
    answer: 'The One Ring is a powerful artifact created by Sauron to control the other Rings of Power and dominate Middle Earth.'
  },
  {
    keywords: /mordor|mount doom|barad[- ]d[uû]r|sauron.*land/i,
    answer: 'Mordor is a dark and barren land in the southeast of Middle Earth, ruled by Sauron and home to Mount Doom.'
  },
  {
    keywords: /hobbits?|shire|frodo|samwise|bilbo|pippin|merry/i,
    answer: 'Hobbits are a small, peaceful people living in the Shire, known for their love of good food, comfort, and simple pleasures. Famous hobbits include Frodo, Samwise, Bilbo, Pippin, and Merry.'
  },
  {
    keywords: /rivendell|elrond|imladris/i,
    answer: 'Rivendell is an Elven refuge in the hidden valley of Imladris, ruled by Elrond and a place of rest and counsel.'
  },
  {
    keywords: /legolas|elf|elves|mirkwood/i,
    answer: 'Legolas is a prince of the Woodland Realm (Mirkwood), a skilled archer, and a member of the Fellowship of the Ring. Elves are immortal beings known for their grace, wisdom, and skill.'
  },
  {
    keywords: /aragorn|strider|king|elessar/i,
    answer: 'Aragorn, also known as Strider and later King Elessar, is the heir of Isildur and rightful king of Gondor. He is a brave leader and a member of the Fellowship.'
  },
  {
    keywords: /gollum|sméagol|precious/i,
    answer: 'Gollum, once known as Sméagol, was corrupted by the One Ring and became obsessed with it, calling it "my precious." He plays a key role in the quest to destroy the Ring.'
  },
  {
    keywords: /galadriel|lorien|lothlórien|lady of light/i,
    answer: 'Galadriel is the Lady of Lothlórien, one of the most powerful and wise Elves in Middle Earth, known for her beauty, wisdom, and gifts to the Fellowship.'
  },
  {
    keywords: /saruman|white wizard|orthanc|isengard/i,
    answer: 'Saruman the White was the head of the Istari order and the White Council, but he was corrupted by a desire for power and allied with Sauron. He resided in Isengard at the tower of Orthanc.'
  },
  {
    keywords: /boromir|gondor|faramir/i,
    answer: 'Boromir was a noble warrior from Gondor and a member of the Fellowship. His brother Faramir also played a key role in defending Gondor.'
  },
  {
    keywords: /rohan|eomer|eowyn|theoden|horse-lords/i,
    answer: 'Rohan, the land of the Horse-lords, is ruled by King Théoden. Éomer and Éowyn are his niece and nephew, both of whom are renowned warriors.'
  },
  {
    keywords: /balrog|moria|khazad-dûm|durin/i,
    answer: 'The Balrog is a powerful ancient demon encountered by the Fellowship in the Mines of Moria (Khazad-dûm), where Gandalf confronts it on the Bridge of Khazad-dûm.'
  },
  {
    keywords: /sauron|dark lord|eye of sauron/i,
    answer: 'Sauron is the primary antagonist of The Lord of the Rings, known as the Dark Lord. He created the One Ring to rule Middle Earth and is symbolized by the Eye of Sauron.'
  },
  {
    keywords: /samwise|sam|gardner/i,
    answer: 'Samwise Gamgee, often called Sam, is Frodo Baggins’ loyal friend and companion. He is known for his courage, loyalty, and love of gardening.'
  },
  {
    keywords: /frodo|baggins/i,
    answer: 'Frodo Baggins is the main protagonist of The Lord of the Rings, a hobbit of the Shire who is entrusted with the task of destroying the One Ring.'
  },
  {
    keywords: /bilbo|hobbiton|there and back again/i,
    answer: 'Bilbo Baggins is the hero of The Hobbit and the uncle of Frodo. He discovers the One Ring during his adventures and later passes it to Frodo.'
  },
  {
    keywords: /nazgûl|ringwraiths|black riders/i,
    answer: 'The Nazgûl, or Ringwraiths, are nine servants of Sauron who were corrupted by Rings of Power and now seek the One Ring.'
  },
  {
    keywords: /mount doom|cracks of doom/i,
    answer: 'Mount Doom is the volcano in Mordor where the One Ring was forged and the only place it can be destroyed.'
  },
  {
    keywords: /middle earth|arda|valinor|beleriand/i,
    answer: 'Middle Earth is the central continent of Tolkien’s legendarium, home to many races and realms. Arda is the world, Valinor is the land of the Valar, and Beleriand is a lost region from the First Age.'
  }
];

export function getMockAnswer(userQuestion: string): string {
  for (const qa of mockChatAnswers) {
    if (qa.keywords.test(userQuestion)) {
      return qa.answer;
    }
  }
  return 'That is a fascinating question! Unfortunately, my memory is a bit foggy on that topic. Try asking about Gandalf, the One Ring, Mordor, Hobbits, Rivendell, or other famous people and places of Middle Earth.';
}
