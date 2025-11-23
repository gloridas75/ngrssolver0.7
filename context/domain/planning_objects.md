# Planning Objects (Python dataclasses recommended)

- **Employee**: id, scheme (A/B/P), productType, gender, skills[], licenses[], primaryOU, preferences, rotationOffset
- **DemandItem**: id, siteOU, role, productType, headcount, shift {start, end, duration}, rotationCode?, skillsRequired[], genderMix?, teamSize?, allowances[]
- **Assignment**: employeeId, demandItemId, date, start, end, teamId?, cost, flags{published,approved,delta}
- **Team**: id, size, roleComposition[], genderMix, siteOU
- **Calendar**: publicHolidays[], planningHorizon {start, end}
