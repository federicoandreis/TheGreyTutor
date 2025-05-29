// Artifacts (duplicate by name/alias/material)
CREATE (a1:Artifact {name: 'Elven Sword', aliases: ['Blade of the Elves'], material: 'Mithril', current_status: 'Lost'})
CREATE (a2:Artifact {name: 'elven sword', aliases: ['Elven Blade'], material: 'mithril', current_status: 'Found'})

// Characters (duplicate by name/alias)
CREATE (c1:Character {name: 'Frodo Baggins', aliases: ['Frodo', 'Ringbearer'], race: 'Hobbit'})
CREATE (c2:Character {name: 'frodo baggins', aliases: ['Frodo', 'Ring Bearer'], race: 'Hobbit', title: 'Mr.'})

// Communities (duplicate by name)
CREATE (com1:Community {name: 'Rivendell', description: 'Elven refuge'})
CREATE (com2:Community {name: 'rivendell', description: 'Hidden valley'})

// Events (duplicate by name/alias)
CREATE (e1:Event {name: 'Battle of Five Armies', aliases: ['The Great Battle'], year: 2941})
CREATE (e2:Event {name: 'battle of five armies', aliases: ['Great Battle'], year: 2941})

// Locations (duplicate by name/alias/material)
CREATE (l1:Location {name: 'Mount Doom', aliases: ['Orodruin'], material: 'Lava'})
CREATE (l2:Location {name: 'mount doom', aliases: ['orodruin'], material: 'lava'})

// Organizations (duplicate by name/alias)
CREATE (o1:Organization {name: 'Fellowship of the Ring', aliases: ['The Nine Walkers']})
CREATE (o2:Organization {name: 'fellowship of the ring', aliases: ['Nine Walkers']})
