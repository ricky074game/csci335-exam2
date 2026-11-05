# 05 - Quicksort and Quickselect (Textbook 7.7 incl. 7.7.6; Sorting slides; HW7; Hoare Partitioning Example handout)

> **Priority: highest of the sorting topics (tracker weight 16).** The professor lists quicksort and quickselect as "will be covered in class (may be the focus of a question on exam)", and names exactly what is testable: *pivot selection methods for quicksort and quickselect* and *the Hoare (and Lomuto?) partition algorithms for quicksort and quickselect*, plus the **complexity of the fundamental operation (partition)**. There are **no sorting-code questions**, so expect: (1) a **partition trace** like the handout (a given pivot, or median-of-3), (2) a full **quicksort or quickselect trace** with median-of-3 and a cutoff (HW7 7.19), (3) complexity/analysis questions (worst/best/average, why a pivot rule is bad, sorted/reverse/equal input), (4) quickselect vs heap-based selection, (5) "design and analyze" questions where quicksort/quickselect is one building block. **Warning from the professor:** answers must follow the TEXTBOOK implementation; a different "valid" partition (e.g. one an AI gives you) is graded wrong.

> **Conventions box - the DEFAULT partition (textbook 7.7.2 = HW7 = the handout = the engine's `hoare` method)**
> 1. Choose the pivot: **median-of-3** = median of `a[left]`, `a[center]`, `a[right]` with `center = (left + right) / 2` (integer division, computed inside the current subarray), or a given index (first / last / random).
> 2. **Swap the pivot with the last element** `a[right]`.
> 3. `i = left`, `j = right - 1`. Move `i` right while `a[i] < pivot`; move `j` left while `a[j] > pivot`. **Both stop on a key equal to the pivot.**
> 4. If `i < j`: swap `a[i]`, `a[j]`, then move on (`i++`, `j--`) and repeat. If `i >= j` (crossed): stop.
> 5. **Swap `a[i]` with the pivot** (at `a[right]`). The pivot is now at its final sorted position `i`; recurse on `left..i-1` and `i+1..right`.
> - **Cutoff (HW7):** a subarray of size **<= 3** is sorted by insertion sort instead (so partitioning only happens when size >= 4).
> - **Quickselect:** k is 1-based. After partitioning with the pivot at index i: `k <= i` -> go left; `k == i + 1` -> the pivot is the answer; otherwise go right.
> - The textbook *code* (Figs 7.16/7.17) is a slightly different routine - see section 5. HW and handout traces use the steps above.

Check any trace with: `python tools/study.py sort partition ARRAY [--pivot median3|first|last|middle|INDEX] [--method hoare|code|lomuto]`, `sort quick ARRAY --cutoff 3`, `sort select ARRAY --k K --cutoff 3`.

---

## 1. The idea, and the simple (not in-place) version

Quicksort is divide and conquer (7.7): to sort S,

1. if |S| is 0 or 1, return;
2. pick any element v (the **pivot**);
3. partition S - {v} into S1 = {x <= v} and S2 = {x >= v};
4. return quicksort(S1), v, quicksort(S2).

After step 3 the pivot is already in its **final sorted position** and S1 and S2 are independent. Like mergesort it solves two subproblems plus linear work for the partition, but the subproblems are **not guaranteed to be the same size** - that is the whole story of its analysis.

The slides' `SortGeneric` (Textbook Fig 7.13) is the idea written naively, using three extra vectors (not in place, not the efficient version):

```cpp
template <typename Comparable>
void SortGeneric(vector<Comparable> &items) {
    if (items.size() <= 1) return;
    vector<Comparable> smaller, same, larger;
    auto chosen_item = items[items.size() / 2];       // pivot is always the middle item
    for (auto &x : items) {
        if (x < chosen_item)       smaller.push_back(std::move(x));
        else if (chosen_item < x)  larger.push_back(std::move(x));
        else                       same.push_back(std::move(x));   // equal keys: a third group, never recursed on
    }
    SortGeneric(smaller);                                           // recursive call
    SortGeneric(larger);                                            // recursive call
    std::move(begin(smaller), end(smaller), begin(items));                      // concatenate back
    std::move(begin(same),    end(same),    begin(items) + smaller.size());
    std::move(begin(larger),  end(larger),  end(items) - larger.size());
}
```

It handles duplicates extremely well (the `same` group is never sorted again), but it allocates O(N) extra memory at every level and copies everything, so it is no better than mergesort. "Classic quicksort" partitions **in place** with two scanning pointers - sections 3 and 5.

---

## 2. Picking the pivot (7.7.1)

| Rule | Cost | Behaviour |
|---|---|---|
| **First element** ("the popular, uninformed choice") | O(1) | fine on random input, **O(N^2) on sorted or reverse-sorted input** (every partition is 0 : N-1). "An absolutely horrible idea." |
| Larger of the first two distinct elements | O(1) | same bad properties |
| **Random element** | one random number (expensive, does not speed up anything else) | safe: no input is bad, only bad luck (exponentially unlikely) |
| **Median-of-3**: median of `a[left]`, `a[center]`, `a[right]` | O(1) (2-3 comparisons) | best estimate of the median at no cost; **good for sorted input** (the center is the true median); about 14% fewer comparisons; deterministic, so bad permutations exist (HW7 7.24) |
| True median | O(N) (quickselect) or worse | would give perfect splits but the selection costs too much |

Worked: `8, 1, 4, 9, 6, 3, 5, 2, 7, 0`: left = 8, right = 0, center = (0 + 9) / 2 = 4 -> a[4] = 6. Median of 8, 6, 0 is **6**. For a sorted array `1..15`: left = 1, center = a[7] = 8, right = 15 -> pivot 8, the exact median, so the split is perfectly balanced. (Median-of-3 ties - two equal candidates - are not specified by the book; the engine prefers center, then left, then right; exam questions should avoid them.)

---

## 3. The Hoare partition of 7.7.2, step by step

### 3.1 Worked example first: the textbook's `8, 1, 4, 9, 6, 3, 5, 2, 7, 0`

Pivot = median-of-3 = 6 (see above). Engine trace:

```
median-of-3: a[0]=8, a[4]=6 (center), a[9]=0 -> pivot 6; swap it with the last element a[9]
    [8 1 4 9 0 3 5 2 7 6]
i stops at index 0, j stops at index 7: swap 8 and 2
    [2 1 4 9 0 3 5 8 7 6]
i stops at index 3, j stops at index 6: swap 9 and 5
    [2 1 4 5 0 3 9 8 7 6]
i stops at index 6 (9), j at index 5 (3): crossed, no swap
    [2 1 4 5 0 3 9 8 7 6]
swap a[6] with the pivot: pivot 6 is now at index 6 (left part 0..5, right part 7..9)
    [2 1 4 5 0 3 6 8 7 9]

final: 2,1,4,5,0,3,6,8,7,9   pivot ends at index 6
```

Reading it with the pictures of the book (`|` marks the hidden pivot):

```
after swapping the pivot 6 with the last element:        8 1 4 9 0 3 5 2 7 | 6
                                                         i               j
i: 8 is not < 6 -> stays at index 0.   j: 7 > 6 -> move; 2 > 6? no -> j stops at index 7.   swap 8 and 2:

                                                         2 1 4 9 0 3 5 8 7 | 6
after the swap both pointers step: i = 1, j = 6.   i skips 1, 4 (both < 6), stops at 9 (index 3).
j: 5 > 6? no -> stops at index 6.   swap 9 and 5:

                                                         2 1 4 5 0 3 9 8 7 | 6
i = 4, j = 5.  i skips 0, 3, stops at 9 (index 6).  j at index 5 (3): not > 6, stops.   i (6) > j (5): CROSSED, no swap.

swap a[i] = 9 with the pivot:                            2 1 4 5 0 3 6 8 7 9
                                                                     ^ pivot, final position 6
```

Left of the pivot (2 1 4 5 0 3) everything is **<= 6**, right of it (8 7 9) everything is **>= 6**. Why: any position left of `i` held a small element originally, or a large one that was replaced during a swap (similarly for the right) - the book's invariant.

### 3.2 The professor's handout (pivot given, position vs index)

"Show the result of partitioning around the randomly chosen pivot at **position 4** (value 9)": `11 2 3 9 10 8 4 12 1 13 5 14`. **Position 4 counts from 1**: the 9 is at **index 3** (0-based). On the exam, if a question says "index" it is 0-based; if it says "position" read the example to see which; when in doubt state which one you used. Engine trace (this is exactly the handout):

```
given pivot index 3 -> pivot 9; swap it with the last element a[11]
    [11 2 3 14 10 8 4 12 1 13 5 9]
i stops at index 0, j stops at index 10: swap 11 and 5
    [5 2 3 14 10 8 4 12 1 13 11 9]
i stops at index 3, j stops at index 8: swap 14 and 1
    [5 2 3 1 10 8 4 12 14 13 11 9]
i stops at index 4, j stops at index 6: swap 10 and 4
    [5 2 3 1 4 8 10 12 14 13 11 9]
i stops at index 6 (10), j at index 5 (8): crossed, no swap
    [5 2 3 1 4 8 10 12 14 13 11 9]
swap a[6] with the pivot: pivot 9 is now at index 6 (left part 0..5, right part 7..11)
    [5 2 3 1 4 8 9 12 14 13 11 10]

final: 5,2,3,1,4,8,9,12,14,13,11,10   pivot ends at index 6
```

Handout rows: (1) pivot 9 swapped to the end `11 2 3 14 10 8 4 12 1 13 5 9`; (2) swap 11 and 5; (3) swap 14 and 1; (4) swap 10 and 4; (5) `i` (at 10) and `j` (at 8) have crossed - the array is unchanged; (6) swap `a[i]` with the pivot: `5 2 3 1 4 8 9 12 14 13 11 10`. Every partition question is graded on **each of these rows**.

### 3.3 The rules, in the order you apply them

1. Pivot to the end (swap, even if it moves another element away from where you expect it).
2. `i` starts at the **first** element, `j` at the **second-to-last**.
3. `i` moves right over elements **strictly smaller** than the pivot, `j` moves left over elements **strictly larger**; each stops on anything else, **including keys equal to the pivot**.
4. If `i < j` swap and step both pointers; otherwise stop.
5. Swap `a[i]` with the pivot. State the pivot's final index and the two subarray ranges.

Cost: i and j together sweep the subarray once: **Theta(N) time** for N elements, O(1) extra space, about N comparisons and at most N/2 swaps.

**Check yourself.** Partition `23 7 15 31 4 19 11 27 2 35 13` around the pivot at **index 7** (value 27).
<details><summary>Answer</summary>

```
given pivot index 7 -> pivot 27; swap it with the last element a[10]
    [23 7 15 31 4 19 11 13 2 35 27]
i stops at index 3, j stops at index 8: swap 31 and 2
    [23 7 15 2 4 19 11 13 31 35 27]
i stops at index 8 (31), j at index 7 (13): crossed, no swap
    [23 7 15 2 4 19 11 13 31 35 27]
swap a[8] with the pivot: pivot 27 is now at index 8 (left part 0..7, right part 9..10)
    [23 7 15 2 4 19 11 13 27 35 31]

final: 23,7,15,2,4,19,11,13,27,35,31   pivot ends at index 8
```

Pivot to the end (swap with 13), one swap (31 and 2), crossing at i = 8, j = 7, final swap; the pivot 27 ends at index 8; recursive ranges 0..7 and 9..10.
</details>

---

## 4. Equal elements - why BOTH pointers stop (7.7.2, slides "Important detail")

The question: should `i` stop on a key equal to the pivot? should `j`? Intuition: they should do the same thing, otherwise the partition is biased (if only `i` stops, all equal keys end up in S2). The test case: **all keys equal**.

| Rule | What happens on N equal keys | Time |
|---|---|---|
| **Both stop** (the textbook) | i and j stop at once, swap two equal keys, step on, and **meet in the middle**; the pivot lands in the middle: halves of about N/2 | **O(N log N)** (T(N) = 2T(N/2) + cN) |
| **Neither stops** (needs bounds checks) | no swaps; i runs to the end, so the pivot goes into the next-to-last place: S1 has N-1 keys | **O(N^2)** ("quadratic time to do nothing") |
| **Only i stops** or **only j stops** (7.22c) | all equal keys go to one side; the pivot lands at one end | **O(N^2)** |

Engine: partitioning 8 equal keys around index 0 swaps (0,6), (1,5), (2,4) and puts the pivot at index 3 - a perfectly balanced split of 3 and 4:

```
given pivot index 0 -> pivot 5; swap it with the last element a[7]
    [5 5 5 5 5 5 5 5]
i stops at index 0, j stops at index 6: swap 5 and 5
    [5 5 5 5 5 5 5 5]
i stops at index 1, j stops at index 5: swap 5 and 5
    [5 5 5 5 5 5 5 5]
i stops at index 2, j stops at index 4: swap 5 and 5
    [5 5 5 5 5 5 5 5]
i stops at index 3 (5), j at index 3 (5): crossed, no swap
    [5 5 5 5 5 5 5 5]
swap a[3] with the pivot: pivot 5 is now at index 3 (left part 0..2, right part 4..7)
    [5 5 5 5 5 5 5 5]

final: 5,5,5,5,5,5,5,5   pivot ends at index 3
```

And the slide example (`8 1 6 9 6 3 5 2 7 | 6`: the pivot 6 is already last and there is another 6 in the array); `i` and `j` meet **on** the 6 at index 4 (the case i == j, which counts as crossed):

```
last element -> pivot 6; it is already the last element
    [8 1 6 9 6 3 5 2 7 6]
i stops at index 0, j stops at index 7: swap 8 and 2
    [2 1 6 9 6 3 5 8 7 6]
i stops at index 2, j stops at index 6: swap 6 and 5
    [2 1 5 9 6 3 6 8 7 6]
i stops at index 3, j stops at index 5: swap 9 and 3
    [2 1 5 3 6 9 6 8 7 6]
i stops at index 4 (6), j at index 4 (6): crossed, no swap
    [2 1 5 3 6 9 6 8 7 6]
swap a[4] with the pivot: pivot 6 is now at index 4 (left part 0..3, right part 5..9)
    [2 1 5 3 6 9 6 8 7 6]

final: 2,1,5,3,6,9,6,8,7,6   pivot ends at index 4
```

It is "not as silly as it seems": quicksort is recursive, so with 10,000,000 elements of which 500,000 are equal, some recursive call will eventually see only those 500,000 equal keys. Doing the "useless" swaps is cheaper than risking wildly uneven partitions.

---

## 5. The textbook C++ code (Figs 7.16 and 7.17) and how it differs

```cpp
template <typename Comparable>
const Comparable & median3( vector<Comparable> & a, int left, int right )
{
    int center = ( left + right ) / 2;
    if( a[ center ] < a[ left ] )   std::swap( a[ left ], a[ center ] );
    if( a[ right ]  < a[ left ] )   std::swap( a[ left ], a[ right ] );
    if( a[ right ]  < a[ center ] ) std::swap( a[ center ], a[ right ] );   // now a[left] <= a[center] <= a[right]
    std::swap( a[ center ], a[ right - 1 ] );                               // hide the pivot at right - 1
    return a[ right - 1 ];
}

template <typename Comparable>
void quicksort( vector<Comparable> & a, int left, int right )
{
    if( left + 10 <= right )                              // size >= 11: otherwise insertion sort below
    {
        const Comparable & pivot = median3( a, left, right );
        int i = left, j = right - 1;                      // i, j start one place early: ++i / --j come first
        for( ; ; )
        {
            while( a[ ++i ] < pivot ) { }                 // stops on a[i] >= pivot  (equal keys stop)
            while( pivot < a[ --j ] ) { }                 // stops on a[j] <= pivot  (equal keys stop)
            if( i < j ) std::swap( a[ i ], a[ j ] );
            else break;
        }
        std::swap( a[ i ], a[ right - 1 ] );              // restore the pivot
        quicksort( a, left, i - 1 );                      // sort small elements
        quicksort( a, i + 1, right );                     // sort large elements
    }
    else insertionSort( a, left, right );
}
```

What is different from the 7.7.2 / HW / handout steps:

| | 7.7.2 steps (HW7, handout, engine `hoare`) | Textbook code (Fig 7.16/7.17, engine `code`) |
|---|---|---|
| Pivot selection | median of the three samples; **only the pivot moves** | `median3` **sorts the three samples in place** (smallest to `a[left]`, largest to `a[right]`) |
| Where the pivot waits | swapped to `a[right]` | swapped to **`a[right-1]`** |
| Pointers start | `i = left`, `j = right - 1` | `i = left`, `j = right - 1` but `++i` / `--j` come first, so the first elements examined are `left+1` and `right-2` |
| Sentinels | needs a check so `j` does not go below `left` | `a[left] <= pivot` stops `j`; the pivot at `right-1` stops `i` |
| Final swap | `a[i]` with `a[right]` | `a[i]` with `a[right-1]` |
| Cutoff | HW7: size <= 3 | `left + 10 <= right` (cutoff 10; sizes <= 10 use insertion sort) |

Same array, both methods (both put the pivot 6 at index 6, but the other elements differ!):

```
median3 sorts a[0], a[4], a[9] and hides pivot 6 at a[8]
    [0 1 4 9 7 3 5 2 6 8]
i=3, j=7: swap 9 and 2
    [0 1 4 2 7 3 5 9 6 8]
i=4, j=6: swap 7 and 5
    [0 1 4 2 5 3 7 9 6 8]
i=6, j=5: crossed, no swap
    [0 1 4 2 5 3 7 9 6 8]
swap a[6] with a[8]: pivot 6 at index 6
    [0 1 4 2 5 3 6 9 7 8]

final: 0,1,4,2,5,3,6,9,7,8   pivot ends at index 6
```

(7.7.2 / HW gave `2 1 4 5 0 3 6 8 7 9`.) Use the 7.7.2 steps for traces unless a question says "the implementation in the chapter". Figure 7.18 shows why you cannot "simplify" the loops to start at `left + 1`/`right - 2` with `while (a[i] < pivot) i++`: with `a[i] == a[j] == pivot` it loops forever, which is another reason `++i`/`--j` are written that way. The sorted `a[left] <= pivot <= a[right]` also act as sentinels, so the inner loops need no bounds tests - that tight loop is why quicksort is fast ("an increment/decrement by 1, a test, and a jump"). Note also: choosing the median but *not* sorting the three (Exercise 7.51) produces bad results on some inputs.

---

## 6. Small arrays and the cutoff (7.7.3)

For N <= about 20 quicksort is slower than insertion sort and, being recursive, it reaches such subarrays all the time. So below a **cutoff** the recursion is replaced by insertion sort: saves about **15%**; the book suggests about 10 (anything from 5 to 20). It also avoids degenerate median-of-3 on 1 or 2 elements. In HW7 7.19 the cutoff is **3**: subarrays with at most 3 elements are insertion sorted (the engine's `--cutoff 3`). Careful with the boundary: "cutoff 3" means size **3 is insertion sorted**; size 4 is partitioned. In the book's code `left + 10 <= right` means size >= 11 is partitioned (cutoff 10).

---

<!-- HOLD hw7 -->
## 7. A full trace: HW7 7.19

Sort `3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5` with median-of-3, Hoare partition of 7.7.2 and cutoff 3.

```
quicksort(0, 10)  depth 0
    [3 1 4 1 5 9 2 6 5 3 5]
median-of-3: a[0]=3, a[5]=9 (center), a[10]=5 -> pivot 5; it is already the last element
    [3 1 4 1 5 9 2 6 5 3 5]
i stops at index 4, j stops at index 9: swap 5 and 3
    [3 1 4 1 3 9 2 6 5 5 5]
i stops at index 5, j stops at index 8: swap 9 and 5
    [3 1 4 1 3 5 2 6 9 5 5]
i stops at index 7 (6), j at index 6 (2): crossed, no swap
    [3 1 4 1 3 5 2 6 9 5 5]
swap a[7] with the pivot: pivot 5 is now at index 7 (left part 0..6, right part 8..10)
    [3 1 4 1 3 5 2 5 9 5 6]
quicksort(0, 6)  depth 1
    [3 1 4 1 3 5 2] 5 9 5 6
median-of-3: a[0]=3, a[3]=1 (center), a[6]=2 -> pivot 2; it is already the last element
    [3 1 4 1 3 5 2] 5 9 5 6
i stops at index 0, j stops at index 3: swap 3 and 1
    [1 1 4 3 3 5 2] 5 9 5 6
i stops at index 2 (4), j at index 1 (1): crossed, no swap
    [1 1 4 3 3 5 2] 5 9 5 6
swap a[2] with the pivot: pivot 2 is now at index 2 (left part 0..1, right part 3..6)
    [1 1 2 3 3 5 4] 5 9 5 6
size 2 <= cutoff 3 at 0..1: insertion pass p=1: 1 moves left 0 place(s) to index 1
    [1 1] 2 3 3 5 4 5 9 5 6
quicksort(3, 6)  depth 2
    1 1 2 [3 3 5 4] 5 9 5 6
median-of-3: a[3]=3, a[4]=3 (center), a[6]=4 -> pivot 3; swap it with the last element a[6]
    1 1 2 [3 4 5 3] 5 9 5 6
i stops at index 3 (3), j at index 3 (3): crossed, no swap
    1 1 2 [3 4 5 3] 5 9 5 6
swap a[3] with the pivot: pivot 3 is now at index 3 (left part 3..2, right part 4..6)
    1 1 2 [3 4 5 3] 5 9 5 6
size 3 <= cutoff 3 at 4..6: insertion pass p=5: 5 moves left 0 place(s) to index 5
    1 1 2 3 [4 5 3] 5 9 5 6
size 3 <= cutoff 3 at 4..6: insertion pass p=6: 3 moves left 2 place(s) to index 4
    1 1 2 3 [3 4 5] 5 9 5 6
size 3 <= cutoff 3 at 8..10: insertion pass p=9: 5 moves left 1 place(s) to index 8
    1 1 2 3 3 4 5 5 [5 9 6]
size 3 <= cutoff 3 at 8..10: insertion pass p=10: 6 moves left 1 place(s) to index 9
    1 1 2 3 3 4 5 5 [5 6 9]

final: 1,1,2,3,3,4,5,5,5,6,9
```

How to present this on paper: for each call write the range, the three samples and the pivot, then the array after each swap, then the array after the final swap with the pivot, then the two ranges (as the engine lines show). Notes on this specific trace:
- First call: samples 3 (left), 9 (center, index 5), 5 (right) -> pivot **5**, which is already last. Note that `i` stops on the 5 at index 4 and `j` on a 5 at index 8 - equal keys are swapped (HW7: "do swap elements that are equal to the pivot").
- Third call `(3,6)`: the samples are 3, 3, 4 - two candidates are equal, so "the median" is a 3 in either case. The book does not say which 3 to use (the engine picks the center); the final sorted array is the same either way, only an intermediate array differs. On an exam question you would avoid or state the convention.
- Subarrays of size 2 or 3 (indices 0..1, 4..6, 8..10) are insertion sorted. The result is **1 1 2 3 3 4 5 5 5 6 9**.

---

<!-- /HOLD -->

## 8. Analysis (7.7.5; slides) - learn the telescoping

Let T(N) be the time on N elements with |S1| = i. The partition costs cN (pivot selection is constant):

**T(N) = T(i) + T(N - i - 1) + cN, T(0) = T(1) = 1.**

### 8.1 Worst case: i = 0 every time (the pivot is the minimum or maximum)

T(N) = T(N-1) + cN. Telescope: T(N-1) = T(N-2) + c(N-1), ..., T(2) = T(1) + c*2. Add them all; the T(N-1), ..., T(2) cancel: **T(N) = T(1) + c(N + (N-1) + ... + 2) = Theta(N^2)**. It is the worst possible: at one depth of the recursion all partitions together cost <= cN and the depth is at most N.

Happens for: first-element (or last-element) pivot on sorted/reverse-sorted input; equal keys if the pointers do not stop (7.22b/c); median-of-3 with the *minimum* of the three (HW7 B); a crafted input for any deterministic rule.

### 8.2 Best case: i = N/2 every time

T(N) = 2T(N/2) + cN - the mergesort recurrence. Divide by N: T(N)/N = T(N/2)/(N/2) + c, telescope log N equations: T(N)/N = T(1) + c log N, so **T(N) = cN log N + N = Theta(N log N)**.

### 8.3 Average case: every |S1| in {0, ..., N-1} equally likely (probability 1/N)

1. The average of T(i) is (1/N) * sum_{j=0}^{N-1} T(j), the same for T(N-i-1). So **T(N) = (2/N) sum_{j<N} T(j) + cN**, i.e. **N T(N) = 2 sum_{j<N} T(j) + cN^2**.   (A)
2. Same equation for N-1: **(N-1) T(N-1) = 2 sum_{j<N-1} T(j) + c(N-1)^2**.   (B)
3. (A) - (B): N T(N) - (N-1) T(N-1) = 2 T(N-1) + 2cN - c. Drop the insignificant -c: **N T(N) = (N+1) T(N-1) + 2cN**.
4. Divide by N(N+1) to get a telescoping form: **T(N)/(N+1) = T(N-1)/N + 2c/(N+1)**.
5. Telescope down to T(2)/3 = T(1)/2 + 2c/3 and add: T(N)/(N+1) = T(1)/2 + 2c(1/3 + 1/4 + ... + 1/(N+1)).
6. The sum is a harmonic sum: ln(N+1) + gamma - 3/2 (gamma = 0.577, Euler's constant). So T(N)/(N+1) = O(log N) and **T(N) = O(N log N)**.

Remember where the assumption is used: the "equally likely sizes of S1" assumption is valid for a random-like pivot with this partitioning; strategies that don't preserve the randomness of the subarrays cannot use this analysis.

<!-- HOLD hw7 -->
### 8.4 HW7 7.20-7.24 and B - the answers in one place

**7.20** (the chapter's code, median-of-3 that sorts the samples, cutoff): sorted, reverse-ordered and random input are **all O(N log N)** (sorted: the center is the median, the pointers cross at the center, perfect halves; random: the average-case analysis). (For curiosity: the 7.7.2 swap-the-median-to-the-end version without sorting the samples is *not* safe on reverse-ordered input - Exercise 7.51; the chapter's code is.)

**7.21** pivot rules:

| Pivot | Sorted | Reverse | Random |
|---|---|---|---|
| first element | O(N^2) (S1 empty) | O(N^2) (S2 empty) | O(N log N) avg |
| larger of the first two distinct | O(N^2) (pivot = 2nd smallest) | O(N^2) (pivot = max) | O(N log N) avg |
| random element | O(N log N) expected | O(N log N) expected | O(N log N) expected |
| average of all elements (cost O(N) to compute, same order as the partition) | O(N log N) (mean = median) | O(N log N) | O(N log N) typical; bad for geometrically growing values like 1, N, N^2, ... (only the max exceeds the mean) |

Engine on sorted `1..8` with the first element as pivot: every partition has |S1| = 0 and |S2| = 7, 6, 5, ...:

```
quicksort(0, 7)  depth 0
    [1 2 3 4 5 6 7 8]
first element -> pivot 1; swap it with the last element a[7]
    [8 2 3 4 5 6 7 1]
i stops at index 0 (8), j at index 0 (8): crossed, no swap
    [8 2 3 4 5 6 7 1]
swap a[0] with the pivot: pivot 1 is now at index 0 (left part 0..-1, right part 1..7)
    [1 2 3 4 5 6 7 8]
quicksort(1, 7)  depth 1
    1 [2 3 4 5 6 7 8]
first element -> pivot 2; swap it with the last element a[7]
    1 [8 3 4 5 6 7 2]
i stops at index 1 (8), j at index 1 (8): crossed, no swap
    1 [8 3 4 5 6 7 2]
swap a[1] with the pivot: pivot 2 is now at index 1 (left part 1..0, right part 2..7)
    1 [2 3 4 5 6 7 8]
```

**7.22 all keys equal:** (a) both stop: O(N log N); (b) neither stops (fix: bounds checks so i, j can't run off the array): O(N^2); (c) only i stops (bounds check for j): O(N^2).

**7.23 pivot = middle element:** does **not** make quadratic time unlikely - it is a deterministic rule, so some input always makes the middle element the minimum. For N = 8: `3 7 5 1 2 4 6 8` (middle index 3 = value 1; after the partition the middle of the remaining 7 is again the smallest...). Engine (pivot middle, no cutoff):

```
quicksort(0, 7)  depth 0
    [3 7 5 1 2 4 6 8]
middle element (index 3) -> pivot 1; swap it with the last element a[7]
    [3 7 5 8 2 4 6 1]
i stops at index 0 (3), j at index 0 (3): crossed, no swap
    [3 7 5 8 2 4 6 1]
swap a[0] with the pivot: pivot 1 is now at index 0 (left part 0..-1, right part 1..7)
    [1 7 5 8 2 4 6 3]
quicksort(1, 7)  depth 1
    1 [7 5 8 2 4 6 3]
middle element (index 4) -> pivot 2; swap it with the last element a[7]
    1 [7 5 8 3 4 6 2]
i stops at index 1 (7), j at index 1 (7): crossed, no swap
    1 [7 5 8 3 4 6 2]
swap a[1] with the pivot: pivot 2 is now at index 1 (left part 1..0, right part 2..7)
    1 [2 5 8 3 4 6 7]
```

(The pattern repeats: every partition is 0 : N-1.) Fix: random pivot.

**7.24 a permutation of 20 elements as bad as possible for median-of-3 with cutoff 3.** Median-of-3 returns the *second smallest* of its three samples, so the worst it can do is pick the second smallest of the whole subarray (|S1| = 1, |S2| = N-2): T(N) = T(N-2) + cN = Theta(N^2). To force it, the sampled positions `a[left]`, `a[center]`, `a[right]` must always hold the two smallest remaining values. One such permutation (checked with the engine, bad for both the 7.7.2 steps and the chapter's code):

`2 12 4 19 6 14 8 18 10 1 3 5 7 9 11 13 15 17 20 16`

Partition sizes: **20, 18, 16, 14, 12, 10, 8, 6, 4**, then a size-2 subarray is insertion sorted. First partition (samples a[0] = 2, a[9] = 1, a[19] = 16 -> pivot 2):

```
median-of-3: a[0]=2, a[9]=1 (center), a[19]=16 -> pivot 2; swap it with the last element a[19]
    [16 12 4 19 6 14 8 18 10 1 3 5 7 9 11 13 15 17 20 2]
i stops at index 0, j stops at index 9: swap 16 and 1
    [1 12 4 19 6 14 8 18 10 16 3 5 7 9 11 13 15 17 20 2]
i stops at index 1 (12), j at index 0 (1): crossed, no swap
    [1 12 4 19 6 14 8 18 10 16 3 5 7 9 11 13 15 17 20 2]
swap a[1] with the pivot: pivot 2 is now at index 1 (left part 0..0, right part 2..19)
    [1 2 4 19 6 14 8 18 10 16 3 5 7 9 11 13 15 17 20 12]

final: 1,2,4,19,6,14,8,18,10,16,3,5,7,9,11,13,15,17,20,12   pivot ends at index 1
```

**HW7 Part B - accidentally take the MINIMUM of the three instead of the median.**
- *Correctness:* unaffected. Quicksort sorts correctly with any pivot; only the balance changes.
- *Efficiency:* worse. Sorted input: the minimum of `a[left] < a[center] < a[right]` is `a[left]`, the smallest element of the subarray, so S1 is empty every time: **O(N^2)**. Reverse input: the minimum is `a[right]`, again the smallest: **O(N^2)**. Random input: the minimum of three random elements has expected rank about N/4, so the expected split is 1/4 : 3/4, T(N) = T(N/4) + T(3N/4) + cN = **O(N log N)** but with a bigger constant. You lose exactly the protection that median-of-3 was introduced for.

<!-- /HOLD -->

### 8.5 Summary table

| | Best | Average | Worst | Extra space |
|---|---|---|---|---|
| Quicksort | O(N log N) | O(N log N) | **O(N^2)** | O(log N) stack typical, O(N) worst |
| `partition` | Theta(N) always | | | O(1) |
| Quickselect | O(N) | **O(N)** | **O(N^2)** | O(1) iterative |
| Introsort | O(N log N) | O(N log N) | O(N log N) | O(log N) |

Stack depth: the worst-case recursion depth is N; recursing on the **smaller** side first (and looping on the larger one) bounds the depth by log2 N (Exercises 7.25-7.26); introsort's depth limit (about 2 log N) also bounds it.

---

## 9. Lomuto partition (marked "maybe": the topics page says "Hoare (and Lomuto?)")

Not in the textbook. A single scan: the pivot is the last element; `i = left - 1`; for `j = left .. right-1`: if `a[j] <= pivot`, `i++` and swap `a[i]`, `a[j]`; finally swap `a[i+1]` with the pivot.

```cpp
int lomuto( vector<int> & a, int left, int right )          // pivot = a[right]
{
    int pivot = a[ right ], i = left - 1;
    for( int j = left; j < right; ++j )
        if( a[ j ] <= pivot )
            std::swap( a[ ++i ], a[ j ] );
    std::swap( a[ i + 1 ], a[ right ] );
    return i + 1;                                            // final position of the pivot
}
```

The invariant: `left..i` holds elements <= pivot, `i+1..j-1` holds elements > pivot. Worked example (`--pivot last`; for a different pivot swap it to the end first):

```
last element -> pivot 6; pivot at a[8] (Lomuto)
    [9 4 7 3 10 2 8 5 6]
a[1] <= 6: i -> 0, swap a[0] and a[1]
    [4 9 7 3 10 2 8 5 6]
a[3] <= 6: i -> 1, swap a[1] and a[3]
    [4 3 7 9 10 2 8 5 6]
a[5] <= 6: i -> 2, swap a[2] and a[5]
    [4 3 2 9 10 7 8 5 6]
a[7] <= 6: i -> 3, swap a[3] and a[7]
    [4 3 2 5 10 7 8 9 6]
swap a[4] with the pivot: pivot 6 at index 4
    [4 3 2 5 6 7 8 9 10]

final: 4,3,2,5,6,7,8,9,10   pivot ends at index 4
```

Compared with Hoare: also Theta(N), but it makes about N/2 swaps instead of N/6 on average, **never splits equal keys** (all-equal input sends everything to one side: O(N^2), see below) and is easier to code. Equal keys:

```
last element -> pivot 5; pivot at a[7] (Lomuto)
    [5 5 5 5 5 5 5 5]
a[0] <= 5: i -> 0 (no move needed)
    [5 5 5 5 5 5 5 5]
a[1] <= 5: i -> 1 (no move needed)
    [5 5 5 5 5 5 5 5]
a[2] <= 5: i -> 2 (no move needed)
    [5 5 5 5 5 5 5 5]
a[3] <= 5: i -> 3 (no move needed)
    [5 5 5 5 5 5 5 5]
a[4] <= 5: i -> 4 (no move needed)
    [5 5 5 5 5 5 5 5]
a[5] <= 5: i -> 5 (no move needed)
    [5 5 5 5 5 5 5 5]
a[6] <= 5: i -> 6 (no move needed)
    [5 5 5 5 5 5 5 5]
swap a[7] with the pivot: pivot 5 at index 7
    [5 5 5 5 5 5 5 5]

final: 5,5,5,5,5,5,5,5   pivot ends at index 7
```

The pivot lands at the last index, S1 has N-1 keys - so Lomuto quicksort on all-equal input is O(N^2); changing `<=` to `<` just sends the equal keys the other way.

---

## 10. Quickselect (7.7.6; slides "Linear-Expected-Time for Selection")

**Selection problem:** find the k-th smallest element (k = 1 is the minimum, k = N/2 the median). Heap-based selection (Ch 6): buildHeap O(N) + k deleteMins = **O(N + k log N)**, which is O(N log N) for the median. Sorting is O(N log N). Quickselect is quicksort that makes only **one** recursive call.

### 10.1 Algorithm (slides' form with S1, S2)

`quickselect(S, k)`:
1. If |S| = 1 then k = 1: return that element. (With a cutoff: if |S| <= CUTOFF, sort S and return the k-th smallest.)
2. Pick a pivot v (median-of-3 ...), partition S - {v} into S1 and S2 exactly as in quicksort.
3. If **k <= |S1|**: return `quickselect(S1, k)`. Else if **k == |S1| + 1**: return the pivot (it is the k-th smallest because exactly k-1 elements are smaller). Else return `quickselect(S2, k - |S1| - 1)` (the first |S1| + 1 elements are all smaller, so subtract them).

### 10.2 The textbook code form (Fig 7.19 in our copy) - absolute k

```cpp
template <typename Comparable>
void quickSelect( vector<Comparable> & a, int left, int right, int k )   // k-th smallest ends in a[k-1]
{
    if( left + 10 <= right )
    {
        const Comparable & pivot = median3( a, left, right );
        int i = left, j = right - 1;
        for( ; ; )
        {
            while( a[ ++i ] < pivot ) { }
            while( pivot < a[ --j ] ) { }
            if( i < j ) std::swap( a[ i ], a[ j ] );
            else break;
        }
        std::swap( a[ i ], a[ right - 1 ] );          // restore pivot at index i

        if( k <= i )                                   // only this part changes from quicksort
            quickSelect( a, left, i - 1, k );
        else if( k > i + 1 )
            quickSelect( a, i + 1, right, k );
        // else k == i + 1: the pivot a[i] is the answer, nothing to do
    }
    else
        insertionSort( a, left, right );
}
```

Here `k` stays the rank in the **whole array** (1-based), compared with the **index** `i` (0-based): the pivot at index i has rank i + 1 (relative to the whole array), so `k <= i` means the answer is left of the pivot, `k == i + 1` means it is the pivot. The slides' form passes the relative rank `k - |S1| - 1`; both are the same thing since |S1| = i - left. The engine uses the absolute form (so do the traces below). When the algorithm ends the k-th smallest is in `a[k-1]`; the array is only partially reordered.

### 10.3 Worked traces (slide array `8 1 4 9 6 3 5 2 7 0`, median-of-3, cutoff 3)

**k = 7** (the slides' example): the first partition puts the pivot 6 at index 6 and `k = 7 = i + 1`, so **6 is the answer** immediately ("if k was 7, then the solution is the pivot").

```
quickSelect(0, 9, k=7)
    [8 1 4 9 6 3 5 2 7 0]
median-of-3: a[0]=8, a[4]=6 (center), a[9]=0 -> pivot 6; swap it with the last element a[9]
    [8 1 4 9 0 3 5 2 7 6]
i stops at index 0, j stops at index 7: swap 8 and 2
    [2 1 4 9 0 3 5 8 7 6]
i stops at index 3, j stops at index 6: swap 9 and 5
    [2 1 4 5 0 3 9 8 7 6]
i stops at index 6 (9), j at index 5 (3): crossed, no swap
    [2 1 4 5 0 3 9 8 7 6]
swap a[6] with the pivot: pivot 6 is now at index 6 (left part 0..5, right part 7..9)
    [2 1 4 5 0 3 6 8 7 9]
k = 7 == i + 1 = 7 -> the pivot 6 is the answer
    [2 1 4 5 0 3 6 8 7 9]

final: 2,1,4,5,0,3,6,8,7,9   k=7 smallest = 6
```

**k = 3** (the slides: "if k = 3 you should look in S1"): 3 <= i = 6 -> left part 0..5; second partition pivot 3 at index 3, 3 <= 3 -> left again; the size-3 subarray is insertion sorted and the answer is a[2].

```
quickSelect(0, 9, k=3)
    [8 1 4 9 6 3 5 2 7 0]
median-of-3: a[0]=8, a[4]=6 (center), a[9]=0 -> pivot 6; swap it with the last element a[9]
    [8 1 4 9 0 3 5 2 7 6]
i stops at index 0, j stops at index 7: swap 8 and 2
    [2 1 4 9 0 3 5 8 7 6]
i stops at index 3, j stops at index 6: swap 9 and 5
    [2 1 4 5 0 3 9 8 7 6]
i stops at index 6 (9), j at index 5 (3): crossed, no swap
    [2 1 4 5 0 3 9 8 7 6]
swap a[6] with the pivot: pivot 6 is now at index 6 (left part 0..5, right part 7..9)
    [2 1 4 5 0 3 6 8 7 9]
k = 3 <= i = 6 -> recurse LEFT on 0..5
    [2 1 4 5 0 3] 6 8 7 9
quickSelect(0, 5, k=3)
    [2 1 4 5 0 3] 6 8 7 9
median-of-3: a[0]=2, a[2]=4 (center), a[5]=3 -> pivot 3; it is already the last element
    [2 1 4 5 0 3] 6 8 7 9
i stops at index 2, j stops at index 4: swap 4 and 0
    [2 1 0 5 4 3] 6 8 7 9
i stops at index 3 (5), j at index 2 (0): crossed, no swap
    [2 1 0 5 4 3] 6 8 7 9
swap a[3] with the pivot: pivot 3 is now at index 3 (left part 0..2, right part 4..5)
    [2 1 0 3 4 5] 6 8 7 9
k = 3 <= i = 3 -> recurse LEFT on 0..2
    [2 1 0] 3 4 5 6 8 7 9
size 3 <= cutoff 3 at 0..2: insertion pass p=1: 1 moves left 1 place(s) to index 0
    [1 2 0] 3 4 5 6 8 7 9
size 3 <= cutoff 3 at 0..2: insertion pass p=2: 0 moves left 2 place(s) to index 0
    [0 1 2] 3 4 5 6 8 7 9
k = 3: answer a[2] = 2
    [0 1 2] 3 4 5 6 8 7 9

final: 0,1,2,3,4,5,6,8,7,9   k=3 smallest = 2
```

**k = 9** ("if k = 9 you should look in S2"): 9 > i + 1 = 7 -> right part 7..9, size 3, insertion sort, the answer is a[8] = 8:

```
quickSelect(0, 9, k=9)
    [8 1 4 9 6 3 5 2 7 0]
median-of-3: a[0]=8, a[4]=6 (center), a[9]=0 -> pivot 6; swap it with the last element a[9]
    [8 1 4 9 0 3 5 2 7 6]
i stops at index 0, j stops at index 7: swap 8 and 2
    [2 1 4 9 0 3 5 8 7 6]
i stops at index 3, j stops at index 6: swap 9 and 5
    [2 1 4 5 0 3 9 8 7 6]
i stops at index 6 (9), j at index 5 (3): crossed, no swap
    [2 1 4 5 0 3 9 8 7 6]
swap a[6] with the pivot: pivot 6 is now at index 6 (left part 0..5, right part 7..9)
    [2 1 4 5 0 3 6 8 7 9]
k = 9 > i + 1 = 7 -> recurse RIGHT on 7..9
    2 1 4 5 0 3 6 [8 7 9]
size 3 <= cutoff 3 at 7..9: insertion pass p=8: 7 moves left 1 place(s) to index 7
    2 1 4 5 0 3 6 [7 8 9]
size 3 <= cutoff 3 at 7..9: insertion pass p=9: 9 moves left 0 place(s) to index 9
    2 1 4 5 0 3 6 [7 8 9]
k = 9: answer a[8] = 8
    2 1 4 5 0 3 6 [7 8 9]

final: 2,1,4,5,0,3,6,7,8,9   k=9 smallest = 8
```

A longer one (11 elements, k = 3: right, then left, then left):

```
quickSelect(0, 10, k=3)
    [17 4 22 9 13 1 30 8 26 15 3]
median-of-3: a[0]=17, a[5]=1 (center), a[10]=3 -> pivot 3; it is already the last element
    [17 4 22 9 13 1 30 8 26 15 3]
i stops at index 0, j stops at index 5: swap 17 and 1
    [1 4 22 9 13 17 30 8 26 15 3]
i stops at index 1 (4), j at index 0 (1): crossed, no swap
    [1 4 22 9 13 17 30 8 26 15 3]
swap a[1] with the pivot: pivot 3 is now at index 1 (left part 0..0, right part 2..10)
    [1 3 22 9 13 17 30 8 26 15 4]
k = 3 > i + 1 = 2 -> recurse RIGHT on 2..10
    1 3 [22 9 13 17 30 8 26 15 4]
quickSelect(2, 10, k=3)
    1 3 [22 9 13 17 30 8 26 15 4]
median-of-3: a[2]=22, a[6]=30 (center), a[10]=4 -> pivot 22; swap it with the last element a[10]
    1 3 [4 9 13 17 30 8 26 15 22]
i stops at index 6, j stops at index 9: swap 30 and 15
    1 3 [4 9 13 17 15 8 26 30 22]
i stops at index 8 (26), j at index 7 (8): crossed, no swap
    1 3 [4 9 13 17 15 8 26 30 22]
swap a[8] with the pivot: pivot 22 is now at index 8 (left part 2..7, right part 9..10)
    1 3 [4 9 13 17 15 8 22 30 26]
k = 3 <= i = 8 -> recurse LEFT on 2..7
    1 3 [4 9 13 17 15 8] 22 30 26
quickSelect(2, 7, k=3)
    1 3 [4 9 13 17 15 8] 22 30 26
median-of-3: a[2]=4, a[4]=13 (center), a[7]=8 -> pivot 8; it is already the last element
    1 3 [4 9 13 17 15 8] 22 30 26
i stops at index 3 (9), j at index 2 (4): crossed, no swap
    1 3 [4 9 13 17 15 8] 22 30 26
swap a[3] with the pivot: pivot 8 is now at index 3 (left part 2..2, right part 4..7)
    1 3 [4 8 13 17 15 9] 22 30 26
k = 3 <= i = 3 -> recurse LEFT on 2..2
    1 3 [4] 8 13 17 15 9 22 30 26
k = 3: answer a[2] = 4
    1 3 [4] 8 13 17 15 9 22 30 26

final: 1,3,4,8,13,17,15,9,22,30,26   k=3 smallest = 4
```

### 10.4 Analysis

- **Worst case** (pivot always the min or max, e.g. sorted input and the first-element pivot with k near the end): **T(N) = T(N-1) + cN = O(N^2)** - the same as quicksort ("quickselect is not really saving a recursive call").
- **Average case** (|S1| equally likely 0..N-1): T(N) = (1/N) sum_{j<N} T(j) + cN (only one of S1, S2 is searched, so the factor is 1/N instead of the 2/N of quicksort). Multiply by N, subtract the equation for N-1: N T(N) - (N-1) T(N-1) = T(N-1) + 2cN - c, so **N T(N) = N T(N-1) + 2cN**, i.e. **T(N) = T(N-1) + 2c**, which gives **T(N) = O(N)**. (In quicksort the factor (N+1)/N made the sum harmonic; here it disappears.) Textbook Exercise 7.30 is this recurrence.
- Intuition: each step discards a constant fraction on average, so the work is cN + cN/2 + cN/4 + ... <= 2cN.
- **Versus heap-based selection:** quickselect's average **O(N)** beats the heap's **O(N + k log N)**; the median (k = N/2) is O(N) average with quickselect and O(N log N) with the heap. The heap method is better when k is tiny (O(N) for k = O(1)) and gives a worst-case guarantee. STL: `std::nth_element` (average O(N)); the guaranteed-linear algorithm is Chapter 10.

---

## 11. Introsort (one paragraph; full details in notes/06)

`std::sort` is typically **introsort**: quicksort with median-of-3 that switches to **heapsort** when the recursion depth exceeds about 2 log N (so the worst case is O(N log N), not O(N^2)) and uses **insertion sort** on small subarrays (the leftover work is O(N): about N/c blocks of cost c^2 each). All three parts are in place, so introsort is in place; it is not stable. See notes/06-heapsort-introsort.md.

---

## 12. Traps that cost points

1. **Position vs index.** The handout says "position 4"; with 1-based positions that is index 3. Say which you use.
2. **Pivot goes to the LAST element** (7.7.2), not the first and not `right-1` (that is the code version). The final swap uses `a[i]` and the pivot.
3. **Both pointers stop on keys equal to the pivot, and equal keys ARE swapped.** After a swap both pointers step (i++, j--) before scanning again.
4. **Median-of-3 uses the center of the CURRENT subarray**, `(left + right) / 2`, not of the whole array.
5. **Cutoff 3 means sizes 0..3 go to insertion sort**; size 4 is partitioned. Do not run a partition on size 2 or 3 when the cutoff says insertion sort.
6. **Partition is Theta(N), never "O(log N)".** Quicksort best case is O(N log N), not O(N).
7. **Quickselect is O(N) average, O(N^2) worst - not O(N log N).** It makes one recursive call; k is 1-based; the answer ends at `a[k-1]`.
8. **Quickselect ranks:** after the partition the right call searches for rank `k - |S1| - 1` (slides) or the same absolute `k` (code). Do not mix the two.
9. **Don't claim a sorted input is bad for median-of-3** (it is perfect) and don't claim a sorted input is fine for the first element (it is O(N^2)).
10. **"Average case" means the stated assumption** (all sizes of S1 equally likely). It is not "typical data".
11. **Quicksort is not stable**; it is in place apart from the recursion stack (O(log N) typical).
12. **Do not use another partition scheme** (e.g. the "pivot stays at the front, one pointer" or a three-way partition) on an exam trace: only 7.7.2 (and maybe Lomuto if the question names it).

---

## 13. What the exam asks and mini-quiz

- **Partition trace:** a given array and pivot (index or median-of-3): show the array after the pivot move, each swap, crossing, final swap, and the final pivot index (6-10 points).
- **Quicksort / quickselect trace** with cutoff 3 and median-of-3 (10-12 points); for quickselect also say which side and why.
- **Complexity and reasoning:** why a pivot rule is bad, behaviour on sorted/reverse/equal input, worst/best/average recurrences, why the average is O(N log N), quickselect vs heap selection, what introsort fixes.
- **Cumulative design:** use `nth_element`/quickselect, `sort`, heaps or hashing together and analyze (see bank/quicksort.json for k-smallest and median designs).

**Mini-quiz.**
1. Name the pivot, its final index and the array after partitioning `9 4 7 3 10 2 8 5 6` with median-of-3. <details><summary>Answer</summary>

```
median-of-3: a[0]=9, a[4]=10 (center), a[8]=6 -> pivot 9; swap it with the last element a[8]
    [6 4 7 3 10 2 8 5 9]
i stops at index 4, j stops at index 7: swap 10 and 5
    [6 4 7 3 5 2 8 10 9]
i stops at index 7 (10), j at index 6 (8): crossed, no swap
    [6 4 7 3 5 2 8 10 9]
swap a[7] with the pivot: pivot 9 is now at index 7 (left part 0..6, right part 8..8)
    [6 4 7 3 5 2 8 9 10]

final: 6,4,7,3,5,2,8,9,10   pivot ends at index 7
```

The samples are a[0] = 9, a[4] = 10 (center = (0 + 8) / 2 = 4), a[8] = 6, so the median and pivot is **9**; it is swapped with the last element 6; one swap (10 and 5); the pointers cross; the pivot ends at **index 7**; result `6 4 7 3 5 2 8 | 9 | 10`.
</details>
2. What is the running time of quicksort on `N` equal keys with the textbook partition, and with a partition where neither pointer stops? <details><summary>Answer</summary>O(N log N) when both stop (balanced halves); O(N^2) when neither stops (S1 gets N-1 keys).</details>
3. Quickselect on N = 11 elements, partition leaves the pivot at index 5: where do you go for k = 3, 6, 9? <details><summary>Answer</summary>k = 3 <= 5: left (range left..4); k = 6 = i + 1: the pivot is the answer; k = 9 > 6: right (range 6..right); in the slides' relative form the rank is 9 - 5 - 1 = 3 in S2.</details>
4. Why is the average-case quickselect O(N) but quicksort O(N log N)? <details><summary>Answer</summary>Quickselect keeps only one side: T(N) = T(N-1) + 2c after the subtraction step (no harmonic sum), so O(N); quicksort keeps both: T(N)/(N+1) = T(N-1)/N + 2c/(N+1), a harmonic sum, so O(N log N).</details>
5. Median-of-3 accidentally takes the minimum of the three; what breaks? <details><summary>Answer</summary>Nothing about correctness; sorted and reverse inputs become O(N^2) because S1 is empty each time; random input stays O(N log N) with a larger constant.</details>

(More practice: `bank/quicksort.json` (38 questions); fresh traces: `python tools/study.py sort random partition|quicksort|quickselect`.)
