# complexity

## scala
* 10% most basic system with a node having a power plant and a demand
* 15% 3 node system, each having the same power plant and the same demand
* 25% 3 node system, each having the same 4 power plants and the same demand
* 30% 3 node system, same 3 renewable power plants are implemented to 25%
* 40% 3 node system, same PP & rPP, but different demand
* 50% 3 node system, same amount of PP & rPP as 40%, but different specification (capacity, costs, etc...)
* 51% 7 more systems are implemented to 50%

## code 

10% - `Nd_0[PP_0] & Nd_0[Dmd_0]`\
15% - `Nd_i[PP_0] & Nd_i[Dmd_0] // i=0,1,2`\
25% - `Nd_i[PP_j] & Nd_i[Dmd_0] // i=0,1,2 // j=0,1,2,3`\
30% - `Nd_i[PP_j] & Nd_i[rPP_i] & Nd_i[Dmd_0] // i=0,1,2 // j=0,1,2,3`\
40% - `Nd_i[PP_j] & Nd_i[rPP_i] & Nd_i[Dmd_0[i]] // i=0,1,2 // j=0,1,2,3`\
50% - `Nd_i[PP_j[i]] & Nd_i[rPP_i[i]] & Nd_i[Dmd_0[i]] // i=0,1,2 // j=0,1,2,3`\
51% - `Nd_x[PP_j[x]] & Nd_x[rPP_i[x]] & Nd_x[Dmd_0[x]] x=0-10 // i=0,1,2 // j=0,1,2,3`

## legend
* PP: Power Plant
* rPP: Renewable Power Plant
* Dmd: Demand
* Nd: Node-Area-Region

## example with 50% complexity

`Nd_0[PP_0[0],PP_1[0],PP_2[0],PP_3[0]] & Nd_0[rPP_0[0],rPP_1[0],rPP_2[0]] & Nd_0[Dmd_0[0]]`\
`Nd_1[PP_0[1],PP_1[1],PP_2[1],PP_3[1]] & Nd_1[rPP_0[1],rPP_1[1],rPP_2[1]] & Nd_1[Dmd_0[1]]`\
`Nd_2[PP_0[2],PP_1[2],PP_2[2],PP_3[2]] & Nd_2[rPP_0[2],rPP_1[2],rPP_2[2]] & Nd_2[Dmd_0[2]]`
