# complexity

## scala
* 10% most basic system with a node having a power plant and a demand
* 15% 3 node system, each having the same power plant and the same demand
* 25% 3 node system, each having the same 4 power plants and the same demand
* 30% 3 node system, same 3 renewable power plants are implemented to 25%
* 40% 3 node system, same PP & rPP, but different demand
* 50% 3 node system, same amount of PP & rPP as 40%, but different specification (capacity, costs, etc...)

## code 

10% - `Nd_0[PP_0] & Nd_0[Dmd]`\
15% - `Nd_i[PP_0] & Nd_i[Dmd] // i=0,1,2`\
25% - `Nd_i[PP_j] & Nd_i[Dmd] // i=0,1,2 // j=0,1,2,3`\
30% - `Nd_i[PP_j] & Nd_i[rPP_i] & Nd_i[Dmd] // i=0,1,2 // j=0,1,2,3`\
40% - `Nd_i[PP_j] & Nd_i[rPP_i] & Nd_i[Dmd[i]] // i=0,1,2 // j=0,1,2,3`\
50% - `Nd_i[PP_j[i]] & Nd_i[rPP_i[i]] & Nd_i[Dmd[i]] // i=0,1,2 // j=0,1,2,3`

## legend
* PP: Power Plant
* rPP: Renewable Power Plant
* Dmd: Demand
* Nd: Node-Area-Region
