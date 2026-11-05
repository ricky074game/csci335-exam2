# 06 - Heapsort and Introsort (Textbook 7.5, Sorting slides "Heapsort" and "Introsort", HW7 7.11 / 7.12 / C)

> **Priority: high.** Heapsort and introsort are two of the four sorts the professor calls "the focus" (with quicksort and quickselect). The topics page lists "complexity of heapsort's fundamental operations
> (buildHeap, deleteMax)", "the efficient (**in-place**) heapsort implementation", and introsort. Expect: a heapsort trace (array after buildHeap, then after each deleteMax), the
> **heapsort complexity analysis** (the professor's own model answer is the first question of the Complexity Analysis Practice Questions: copy its structure), in-place/stability facts,
> and introsort's three parts with the O(n log n) argument. **No sorting code is asked on the exam** (Project 3), but `myHeapSort` (HW7 C) uses library calls, so know it.
> Background: `03-heaps.md` (Chapter 6 heaps). **Warning (professor):** use the textbook's heapsort, not one from a chatbot; the layout differs from Chapter 6.

**Conventions (textbook Fig 7.10; any other variant is graded wrong):**

| Item | Heapsort (Ch 7, Fig 7.10) | Binary heap (Ch 6, note 03) |
|---|---|---|
| Heap kind | **MAX**-heap (so the array ends up ascending) | **MIN**-heap |
| First element at | **index 0** (it is the data array itself) | index 1 (index 0 = scratch / sentinel) |
| left child of i | **2i + 1** (`leftChild`) | 2i |
| right child of i | **2i + 2** | 2i + 1 |
| parent of i | (i - 1) / 2 | i / 2 |
| buildHeap loop | `i = n/2 - 1` down to `0`: `percDown(a, i, n)` | `i = currentSize/2` down to `1` |
| last internal node / leaves | `n/2 - 1`; leaves are `n/2 .. n-1` | `N/2`; leaves `N/2+1 .. N` |
| deleteMax | `swap(a[0], a[j])` then `percDown(a, 0, j)`, for `j = n-1` down to `1` | last element to the root, size--, `percolateDown(1)` |
| Size argument | `n` = logical heap size passed to `percDown` | member `currentSize` |
| Temp value | local `tmp` | local `tmp` (HW6 trace shows it in index 0) |

---

## 1. The idea, by example (Fig 7.6-7.9): sort 31, 41, 59, 26, 53, 58, 97

Textbook 7.5 starts from Ch 6: build a heap of N elements (O(N)), then do N deleteMins (smallest comes out first); recording the outputs in a second array doubles the memory. The trick: after each
deleteMin the heap shrinks by one, so the freed last cell can hold the element that just left. Keep a **max**-heap and the array ends up **ascending**: each deleteMax puts the current maximum at the end of the heap region.
The array is always `[ heap part | sorted part ]`.

Engine trace (0-indexed max-heap, **array after every step**):

```
$ python tools/study.py heap sort 31,41,59,26,53,58,97
heapsort 31,41,59,26,53,58,97  (textbook Fig. 7.10: 0-indexed max-heap)

  31 41 59 26 53 58 97                     # start (n = 7); buildHeap: percDown from i = 2 down to 0 (MAX-heap, 0-indexed)
  31 41 97 26 53 58 59                     # buildHeap: after percDown(a, 2, 7) (value 59)
  31 53 97 26 41 58 59                     # buildHeap: after percDown(a, 1, 7) (value 41)
  97 53 59 26 41 58 31                     # buildHeap: after percDown(a, 0, 7) (value 31)
  97 53 59 26 41 58 31                     # == heap built ==
  59 53 58 26 41 31 97                     # deleteMax 97: swap a[0] with a[6], then percDown(a, 0, 6) -> heap = a[0..5], sorted = a[6..6]
  58 53 31 26 41 59 97                     # deleteMax 59: swap a[0] with a[5], then percDown(a, 0, 5) -> heap = a[0..4], sorted = a[5..6]
  53 41 31 26 58 59 97                     # deleteMax 58: swap a[0] with a[4], then percDown(a, 0, 4) -> heap = a[0..3], sorted = a[4..6]
  41 26 31 53 58 59 97                     # deleteMax 53: swap a[0] with a[3], then percDown(a, 0, 3) -> heap = a[0..2], sorted = a[3..6]
  31 26 41 53 58 59 97                     # deleteMax 41: swap a[0] with a[2], then percDown(a, 0, 2) -> heap = a[0..1], sorted = a[2..6]
  26 31 41 53 58 59 97                     # deleteMax 31: swap a[0] with a[1], then percDown(a, 0, 1) -> heap = a[0..0], sorted = a[1..6]

sorted: 26,31,41,53,58,59,97
```


How to read it:

- **buildHeap**: `n = 7`, last internal node `n/2 - 1 = 2`. `percDown(a, 2, 7)`: 59 has children 58 and 97 (indices 5 and 6); 97 is larger and bigger than 59, so 97 goes up. `percDown(a, 1, 7)`: 41 has children 26 and 53; 53 is larger; 53 goes up.
  `percDown(a, 0, 7)`: 31 has children 53 and 97; 97 is larger; 97 goes up; at index 2 the children are 58 and 59; 59 is larger and bigger than 31; 59 goes up; 31 lands at index 6. Heap = `97 53 59 26 41 58 31` (book Fig 7.8).
- **deleteMax** (`j = 6`): swap `a[0]` and `a[6]` (97 goes to its final place, array `31 53 59 26 41 58 | 97`), then `percDown(a, 0, 6)` fixes the shrunken heap `a[0..5]`: 59 moves up, then 58, and 31 lands at index 5. Result `59 53 58 26 41 31 | 97` (book Fig 7.9).
- Each further deleteMax moves the next-largest value just left of the sorted region. After `j = 1` (heap of size 1) the array is sorted; **no deleteMax is needed for the last element**, which is why the loop runs `j = n-1 .. 1` (n - 1 deleteMaxes).

> *A worked HW7 answer goes here. It is added to the public version after HW7 is due (Nov 17).*

## 2. Do not mix this up with the Chapter 6 heap

Same 7 numbers, built as a **max**-heap in each layout:

```
$ python tools/study.py heap build 31,41,59,26,53,58,97 --max
buildHeap (max-heap)

  [0]=- | 31 41 59 26 53 58 97                   # start (size 7); percolateDown from i = 3 down to 1
  [0]=- | 31 41 97 26 53 58 59                   # after percolateDown(3) (value 59)
  [0]=- | 31 53 97 26 41 58 59                   # after percolateDown(2) (value 41)
  [0]=- | 97 53 59 26 41 58 31                   # after percolateDown(1) (value 31)

final heap (from index 1): 97,53,59,26,41,58,31
```


The values come out the same (`97 53 59 26 41 58 31`), but in the Ch 6 layout they sit in cells **1..7** (cell 0 scratch, children `2i, 2i+1`), while in heapsort they sit in cells **0..6** (children `2i+1, 2i+2`).
The book says it directly: "unlike the binary heap, where the data begin at array index 1, the array for heapsort contains data in position 0. Thus the code is a little different."
Why? Heapsort sorts **in place in the caller's array**, whose data start at index 0 and which has no spare cell 0; no copy of the data into a separate 1-indexed heap object is allowed (that would cost O(n) extra space).
On the exam, if the question says "heapsort", use `2i+1` / `n/2 - 1`; if it says "binary heap / priority queue / deleteMin", use `2i` / `N/2`.

---

## 3. The code (Fig 7.10), line by line

```cpp
1  /** Standard heapsort. */
4  template <typename Comparable>
5  void heapsort( vector<Comparable> & a )
6  {
7      for( int i = a.size( ) / 2 - 1; i >= 0; --i )   /* buildHeap */
8          percDown( a, i, a.size( ) );
9      for( int j = a.size( ) - 1; j > 0; --j )
10     {
11         std::swap( a[ 0 ], a[ j ] );                  /* deleteMax */
12         percDown( a, 0, j );
13     }
14 }

21 inline int leftChild( int i )
22 {
23     return 2 * i + 1;
24 }

31 template <typename Comparable>
32 void percDown( vector<Comparable> & a, int i, int n )
33 {
34     int child;
35     Comparable tmp;
36
37     for( tmp = std::move( a[ i ] ); leftChild( i ) < n; i = child )
38     {
39         child = leftChild( i );
40         if( child != n - 1 && a[ child ] < a[ child + 1 ] )
41             ++child;                                   // the LARGER child
42         if( tmp < a[ child ] )
43             a[ i ] = std::move( a[ child ] );          // larger child moves UP
44         else
45             break;
46     }
47     a[ i ] = std::move( tmp );
48 }
```

- **Lines 7-8 (buildHeap):** start at the last internal node `n/2 - 1` and percolate down toward index 0. Leaves (`n/2 .. n-1`) need nothing. O(n).
- **Lines 9-13 (n-1 deleteMaxes):** `a[0]` is the maximum of the heap region `a[0..j]`. Swapping it with `a[j]` puts it in its final sorted cell, and shrinks the heap region to `a[0..j-1]` (the heap size passed to `percDown` is `j`).
  The element now at the root (the old `a[j]`) is probably small, so it percolates down. That is the "deleteMax" and there is **no separate output array**.
- **Line 37:** `tmp` is the value being moved (like index 0 in HW6); `leftChild(i) < n` means "i has at least a left child inside the heap of size n".
- **Line 40:** `child != n - 1` means the left child is the last element of the heap, so there is **no right child**. Then `a[child] < a[child+1]` picks the **larger** child; **equal children: the left one is kept** (strict `<`).
- **Line 42:** `tmp < a[child]` strict: stop on equal.
- Everything is O(1) extra space: `child`, `tmp`, and the loop variables. No recursion, no second array.

**Check yourself**
1. What does `percDown(a, 0, 1)` do? 2. Which argument to `percDown` changes inside the second loop, and why? 3. Parent of index 9 in a 0-indexed heap?

<details><summary>Answer</summary>

1. Nothing: `leftChild(0) = 1 < 1` is false, so the loop body never runs and `a[0] = tmp`. 2. `n` (the third argument `j`): the heap shrinks by one every iteration, so cells `a[j..]` are no longer part of the heap. 3. (9 - 1)/2 = 4.
</details>

---

## 4. Analysis (7.5.1 and the professor's model answer)

**The professor's model answer (Complexity Analysis Practice Questions, Q1: use this wording as your template):**

> "Heapsort starts with an unsorted array, then builds a max heap (heapifies) in O(n) time. It then iteratively pops the largest element from the top of the heap, fixes the heap, and puts it where the last heap element used to be, thus increasing the sorted portion at the end of the array by 1 and decreasing the size of the heap by 1.
> We do this for all n elements, and the time for popping the max element of a heap, including fixing the heap, is O(log n). Thus O(n) buildheap + (n * O(log n)) for n deletemax = **O(n log n)** total time."

Structure to reproduce: (1) name the steps; (2) cost of each step with a reason; (3) loops multiply, steps add; (4) conclusion as a **tight** bound.

| Part | Cost | Why |
|---|---|---|
| buildHeap | **O(n)** (< 2n comparisons) | sum of heights of the nodes < n (note 03, section 5); not n log n |
| one deleteMax = swap + `percDown(a,0,j)` | **O(log n)** worst case (<= 2 log j comparisons) | the moved element sinks at most the height floor(log2 j) |
| n - 1 deleteMaxes | O(n log n) | (n-1) x O(log n); the i-th costs at most 2 log(n - i + 1) comparisons |
| **Total** | **O(n) + O(n log n) = O(n log n)** worst, average, and best (for distinct keys) | the larger term dominates |
| Extra space | **O(1)** | in place |

- Textbook counts (7.5.1): buildHeap uses **< 2N** comparisons; the i-th deleteMax uses **at most 2 log(N - i + 1)**; total in the worst case **2N log N - O(N)** comparisons (Exercise 7.13: inputs exist where every percDown reaches a leaf).
  On average heapsort does only slightly fewer: 2N log N - O(N log log N) (Thm 7.5). In practice (one measured run on N = 1000 random ints) buildHeap took about 1,900 comparisons and the deleteMax phase about 15,000, so 2N log N (about 20,000) is an upper bound, not an estimate to quote exactly.
  Lower bound: any comparison sort needs Omega(N log N) comparisons, so heapsort is **asymptotically optimal**; the book also proves heapsort uses at least N log N - O(N) comparisons on some inputs.
- **Does the input order matter? (Exercise 7.12: presorted input.)** No, for the Big-O: sorted ascending or descending input is still **O(N log N)**, and in fact Theta(N log N): buildHeap is O(N) either way, and each of the N-1 deleteMaxes moves a small element
  (from the end of the heap) to the root, so it sinks to the bottom again and costs about log N. (Descending input is already a max-heap, so buildHeap does almost no moves; it does not help the second phase.) Unlike insertion sort, heapsort has **no fast best case** on presorted data.
  *Edge case:* if **all keys are equal**, `tmp < a[child]` is always false, every `percDown` stops at once, and heapsort runs in O(N). Do not write this unless asked about equal keys; say "O(N log N) for any input of distinct keys".
- **Compared with mergesort and quicksort:** heapsort's worst case is O(N log N) (quicksort's is O(N^2)) and it needs O(1) space (mergesort needs O(N)); but it is **not stable**, and in practice it is slower than quicksort because it jumps around the array
  (`i` to `2i+1`: poor cache locality) and does about twice as many comparisons per element (2 per level).

| Sort | Worst | Average | Best | Extra space | Stable? | In place? |
|---|---|---|---|---|---|---|
| Insertion | O(n^2) | O(n^2) | O(n) (sorted) | O(1) | yes | yes |
| Mergesort | O(n log n) | O(n log n) | O(n log n) | **O(n)** | **yes** | no (array version) |
| Quicksort | **O(n^2)** | O(n log n) | O(n log n) | O(log n) stack average | no | yes |
| **Heapsort** | **O(n log n)** | O(n log n) | O(n log n) | **O(1)** | **no** | **yes** |
| Introsort (`std::sort`) | **O(n log n)** | O(n log n) | O(n log n) | O(log n) stack | no | yes |

**Why heapsort is not stable (verified example).** Tag equal keys by their input order: input `1a, 2b, 2c` (n = 3). buildHeap: percDown(a,0,3): the children `2b` and `2c` compare equal, so the left child `2b` is used and moves up: heap `2b 1a 2c`.
First deleteMax: swap `a[0]` and `a[2]`: `2c 1a | 2b`; second: swap `a[0]` and `a[1]`: `1a | 2c 2b`. Output `1a, 2c, 2b`: the two 2's came out in **reverse** order. (The long-distance swap of the root with the last element is what breaks stability.)

**Check yourself**
1. Prove heapsort is O(n log n) in the professor's style. 2. Running time on already-sorted input? 3. Why does heapsort not use extra memory but mergesort does? 4. Is heapsort stable?

<details><summary>Answer</summary>

1. buildHeap O(n) (sum of node heights); then n - 1 deleteMaxes, each a swap O(1) plus percDown O(log n) (the moved element sinks at most the height of the heap); steps add, loop multiplies: O(n) + n x O(log n) = O(n log n).
2. Still Theta(n log n): the order of the input does not matter (no best-case shortcut). 3. The sorted output is built in the cells that the shrinking heap freed. 4. No (example above).
</details>

---

> *A worked HW7 answer goes here. It is added to the public version after HW7 is due (Nov 17).*

## 6. Introsort (slides "Introsort", textbook 7.7 intro and Exercise 7.27)

**Introsort (introspective sort)** is a hybrid that gets quicksort's speed on typical inputs *and* a guaranteed O(n log n) worst case. It starts as **quicksort** and
1. **switches to heapsort** on a subarray when the **recursion depth exceeds a limit of about 2 log2 n** (the textbook's Exercise 7.27: pass a `depth` parameter, initially about 2 log N, decrement it per recursive call, and when it reaches 0 call heapsort on the current subarray); and
2. **uses insertion sort** when a subarray is **smaller than a constant threshold** (e.g. 16 or 20), where insertion sort is fastest since it has no recursion, no allocation, no setup (versus buildHeap).

`std::sort` in C++ is typically introsort (so it is O(n log n) worst case, in place, **not stable**; use `std::stable_sort` for stability: a merge-sort variant that wants extra memory). All three components are in place, so introsort is in place.

```
introsort(A, left, right, depthLimit):
    if right - left + 1 < THRESHOLD:  insertion sort A[left..right]   (or leave for one final insertion-sort pass)
    else if depthLimit == 0:          heapsort A[left..right]
    else:                             p = partition(A, left, right)   (median-of-3, Hoare)
                                      introsort(A, left, p-1, depthLimit-1); introsort(A, p+1, right, depthLimit-1)
```
(Sketch only: sorting code is not asked on the exam.)

### Why it is O(n log n) worst case - the three portions (slides "Introsort - Complexity Analysis")

1. **Quicksort portion: O(n log n).** The recursion is stopped at depth about 2 log n. The subarrays at any one depth are disjoint, so the partitions at one depth cost at most O(n) in total; there are at most 2 log n depths: O(n) x 2 log n = **O(n log n)**, however bad the pivots are
   (this is the part that was O(n^2) in plain quicksort).
2. **Heapsort portion: O(n log n).** If a subarray hits the depth limit, heapsort sorts it in O(m log m). The subarrays heapsorted are disjoint, sizes m_1 + m_2 + ... <= n, so the total is at most sum m_i log m_i <= (sum m_i) log n = **O(n log n)**. (Worst case: the whole array is heapsorted.)
   So in the bad case we pay O(n log n) for the quicksort portion plus O(n log n) for the heapsort portion = **O(n log n)**.
3. **Insertion-sort portion: O(n)** (surprising, but true because the threshold c is a **constant**). Slides' example: c = 20, input of 1,000: the worst case is 50 subarrays of size 20, each costing about c^2/2 = 200 steps (insertion sort is quadratic), 50 x 200 = 10,000 steps;
   for 1,000,000 elements: 50,000 subarrays x 200 = 10,000,000 steps. In general **(n / c) subarrays x c^2/2 each = c n / 2 = O(n)** (about c/2 = 10 steps per element, a constant). Proof for sizes s_i <= c with sum s_i = n:
   sum s_i^2/2 <= (c/2) sum s_i = c n / 2.
   If the depth limit is never hit, the quicksort portion alone (depth-bounded, with insertion sort finishing the small pieces) is already O(n log n) by item 1.

**Total: O(n log n) + O(n log n) + O(n) = O(n log n) in the worst case**; on typical inputs it is quicksort's O(n log n) average with the fast constant, and the heapsort branch is rarely taken (it triggers only for adversarial/"median-of-3 killer" inputs).
Stack space: the depth limit keeps the recursion depth at O(log n).

**Why not just use heapsort always?** Slower constants (cache behaviour, 2 comparisons per level). **Why not mergesort?** O(n) extra memory, and `std::sort` is in place. **Why not plain quicksort?** O(n^2) worst case and O(n) stack in the worst case.

| Component | Role | Cost it adds |
|---|---|---|
| Quicksort (median-of-3, Hoare) | fast on average | O(n log n) (depth limited) |
| Heapsort | worst-case guarantee when recursion too deep | O(n log n) |
| Insertion sort (size < c) | speed on tiny subarrays | O(n) total |

**Check yourself**
1. What are the three algorithms in introsort and when does each take over? 2. Prove introsort is O(n log n) worst case. 3. Why is the insertion-sort part O(n), not O(n^2)? 4. Is `std::sort` stable?

<details><summary>Answer</summary>

1. Quicksort by default; heapsort when the recursion depth passes about 2 log n; insertion sort when the subarray size is below a small constant. 2. Quicksort part O(n log n) because the depth is capped at 2 log n and each depth does O(n) partition work; heapsort part at most O(n log n) on disjoint subarrays; insertion part O(n); sum O(n log n).
3. Each insertion sort runs on at most c elements (constant c), costing at most c^2/2; subarrays are disjoint, so there are at most about n/c of them: (n/c)(c^2/2) = cn/2 = O(n). 4. No (`stable_sort` is).
</details>

---

## 7. Traps that cost points

1. **Layout confusion.** Heapsort: 0-indexed, children `2i+1` and `2i+2`, buildHeap starts at `n/2 - 1`. Chapter 6: 1-indexed, `2i`/`2i+1`, starts at `N/2`. Different questions, different formulas.
2. **It is a MAX-heap** (so the output is ascending). A min-heap would give descending order, or need a second array.
3. **The last element is never deleted:** the loop is `j = n - 1 .. 1`; the final remaining element is already in place. n - 1 deleteMaxes, not n.
4. buildHeap is **O(n)**; total heapsort is **O(n log n)** (say both, do not claim the whole thing is O(n)).
5. Not stable. In place with **O(1)** extra space (mergesort is the one with O(n)).
6. Say the cost of `percDown` is O(log n) *worst case* because the swapped-in element sinks (it comes from the bottom).
7. In traces, show `n` shrinking: the sorted region `a[j..n-1]` is **never touched again**.
8. **Introsort:** heapsort takes over by **depth** (about 2 log n), not by array size; insertion sort takes over by **size** (below a constant threshold). The insertion part is O(n) only because the threshold is a constant.
9. Best/worst case of heapsort on sorted input: still n log n (no adaptivity).
10. `std::sort` = introsort (not stable); `std::stable_sort` = mergesort-based.

---

## 8. What the exam asks (and how to answer)

| Likely question | Answer shape |
|---|---|
| Trace heapsort on an array of 6-8 numbers | Array after buildHeap, then after each deleteMax, marking the sorted tail (use the engine format above). |
| Analyze heapsort | Professor's template: O(n) buildHeap + n x O(log n) deleteMax = O(n log n); say in place, not stable. |
| Running time on sorted / reverse sorted input | Still O(n log n); no fast case. |
| Compare heapsort / mergesort / quicksort | Table in section 4 (space, worst case, stability, cache). |
| Describe and analyze introsort | Three parts; each portion's bound; total O(n log n); in place. |
| Write `myHeapSort` using `make_heap`/`pop_heap` (HW7 C) | Section 5 code and the O(n log n) justification. |
| Design question using a sort | Use `std::sort` O(n log n), `priority_queue` push/pop O(log n), `make_heap` O(n). |
