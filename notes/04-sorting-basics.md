# 04 - Sorting Basics (Textbook 7.1-7.3, 7.6, 7.8, 7.9, 7.11 light, 7.12 concepts; Sorting slides; HW7)

> **Priority: medium-high (tracker weight 9).** The topics page calls selection sort, insertion sort and mergesort "background knowledge (may be part of a question on exam)". What is actually fair game: tracing them, their complexities **and the complexity of their fundamental operations** (the merge, one insertion pass), inversions, stability, the decision-tree lower bound, and "which sort would you use". HW7 7.1, 7.2, 7.15, 7.17 are exactly this material. **There are no sorting-code questions** (sorting code is Project 3, after the exam): you need traces, bounds and short proofs, not to write the code. The sorts you will be asked about *in depth* (quicksort, quickselect, heapsort, introsort) are in notes 05 and 06; the master complexity table at the end of this file covers all of them.

**Conventions used everywhere (textbook + professor)**

- N = number of elements, arrays are 0-indexed, sorting is by `<` only (**comparison-based sorting**, Textbook 7.1).
- **Stable** = equal keys keep their input order. **In place** = O(1) (or O(log N) stack) extra memory.
- **Inversion** = a pair (i, j), i < j, with a[i] > a[j]. Equal elements are *not* inversions.
- Big-O answers must be **tight** and justified (loops multiply, steps add). Say average vs worst explicitly.
- Mergesort: `center = (left + right) / 2` (integer division), the left half gets the extra element, `merge` takes from the left run on ties (`<=`).
- Insertion sort: pass p = 1 .. N-1 slides `a[p]` left while `tmp < a[j-1]` (strict `<`).

---

## 1. The STL interface (slides "Sorting algorithms", Textbook 7.1)

```cpp
sort(v.begin(), v.end());                                  // ascending
sort(v.begin(), v.end(), greater<int>{});                  // descending
sort(v.begin(), v.begin() + (v.end() - v.begin()) / 2);    // sorts only the first half
stable_sort(v.begin(), v.end());                           // equal keys keep their order
```

- `std::sort` needs **random-access iterators** (vector, array, deque; **not** `list` - use `lst.sort()`, a mergesort that relinks nodes). It is O(N log N), typically **introsort** (notes 06). **Not stable.**
- `std::stable_sort` is O(N log N) with enough extra memory (typically a mergesort) and **is stable**: "does not swap the positions of two elements with the same comparison key".
- The third argument is a comparator (function object); the algorithms only use `<`-style comparisons.

**Check yourself.** Why does `sort(lst.begin(), lst.end())` not compile for `std::list`? <details><summary>Answer</summary>`std::list` iterators are bidirectional, but `sort` needs random access (it jumps by index/arithmetic). Use `lst.sort()`.</details>

---

## 2. Insertion sort (Textbook 7.2, 7.3; slides; HW7 7.1, 7.2)

### 2.1 Worked example first: Figure 7.1 of the book

Sort `34, 8, 64, 51, 32, 21`. Pass p makes positions 0..p sorted by sliding `a[p]` left past every larger element.

```
insertion pass p=1: 8 moves left 1 place(s) to index 0
    [8 34 64 51 32 21]
insertion pass p=2: 64 moves left 0 place(s) to index 2
    [8 34 64 51 32 21]
insertion pass p=3: 51 moves left 1 place(s) to index 2
    [8 34 51 64 32 21]
insertion pass p=4: 32 moves left 3 place(s) to index 1
    [8 32 34 51 64 21]
insertion pass p=5: 21 moves left 4 place(s) to index 1
    [8 21 32 34 51 64]

final: 8,21,32,34,51,64   9 inversions
```

The "positions moved" column of the book's Figure 7.1 is 1, 0, 1, 3, 4: total **9 moves = the 9 inversions** of the input. 

<!-- HOLD hw7 -->
Now the HW7 7.1 input (with duplicates; notice the equal 1s and 5s never jump over each other):

```
insertion pass p=1: 1 moves left 1 place(s) to index 0
    [1 3 4 1 5 9 2 6 5]
insertion pass p=2: 4 moves left 0 place(s) to index 2
    [1 3 4 1 5 9 2 6 5]
insertion pass p=3: 1 moves left 2 place(s) to index 1
    [1 1 3 4 5 9 2 6 5]
insertion pass p=4: 5 moves left 0 place(s) to index 4
    [1 1 3 4 5 9 2 6 5]
insertion pass p=5: 9 moves left 0 place(s) to index 5
    [1 1 3 4 5 9 2 6 5]
insertion pass p=6: 2 moves left 4 place(s) to index 2
    [1 1 2 3 4 5 9 6 5]
insertion pass p=7: 6 moves left 1 place(s) to index 6
    [1 1 2 3 4 5 6 9 5]
insertion pass p=8: 5 moves left 2 place(s) to index 6
    [1 1 2 3 4 5 5 6 9]

final: 1,1,2,3,4,5,5,6,9   10 inversions
```

<!-- /HOLD -->

### 2.2 The code (Figure 7.2) line by line

```cpp
template <typename Comparable>
void insertionSort( vector<Comparable> & a )
{
    for( int p = 1; p < a.size( ); ++p )          // N-1 passes; a[0..p-1] is already sorted
    {
        Comparable tmp = std::move( a[ p ] );     // lift the new element out (like the "hole" in a heap)
        int j;
        for( j = p; j > 0 && tmp < a[ j - 1 ]; --j )
            a[ j ] = std::move( a[ j - 1 ] );     // shift every larger element one slot to the right
        a[ j ] = std::move( tmp );                // drop tmp into the hole
    }
}
```

- The comparison is the **strict** `tmp < a[j-1]`, so `tmp` stops in front of an equal element: **stable**, and **all-equal input costs only N-1 comparisons** (HW7 7.2: Theta(N)).
- The STL version (Figs 7.3, 7.4) is the same loop written with iterators and a comparator; every statement has a direct counterpart.

### 2.3 Running time and inversions (Theorem 7.1, 7.2)

- Two nested loops, each up to N iterations: **O(N^2) worst case**, tight: reverse-ordered input makes pass p move p positions, 1 + 2 + ... + (N-1) = N(N-1)/2.
- Presorted input: the inner test fails at once, so **O(N)** (one comparison per element).
- Every inner-loop shift removes **exactly one inversion** (swapping two adjacent out-of-order elements removes one inversion, and a sorted array has none). So the number of shifts = I = number of inversions and
  **insertion sort is O(N + I)** - linear if I = O(N), quadratic if I = Theta(N^2). It is the best simple sort on nearly sorted data.

Count inversions with the engine (this is the Textbook 7.3 example, 9 inversions):

```
9 inversions: [(34, 8), (34, 32), (34, 21), (64, 51), (64, 32), (64, 21), (51, 32), (51, 21), (32, 21)]
average for n=6: n(n-1)/4 = 7.5
```

**Theorem 7.1 (average inversions = N(N-1)/4).** Assume distinct elements and all N! permutations equally likely. Take a list L and its reverse L^r. For any pair of values x < y, exactly one of L, L^r has them in the wrong order (y before x). There are C(N,2) = N(N-1)/2 pairs, so inv(L) + inv(L^r) = N(N-1)/2, and the average of the two is N(N-1)/4. Every permutation is paired with its reverse, so the average over all permutations is N(N-1)/4 = Theta(N^2). Example: 34, 8, 64, 51, 32, 21 has 9 inversions; its reverse 21, 32, 51, 64, 8, 34 has 6; 9 + 6 = 15 = 6*5/2. (The slides leave "?" blanks exactly here: total = N(N-1)/2, average = N(N-1)/4.)

**Theorem 7.2 (adjacent swaps are Omega(N^2) on average).** The average input has Omega(N^2) inversions; an adjacent swap changes the inversion count by exactly one; the sorted array has 0. So at least N(N-1)/4 swaps are needed on average. This covers insertion sort, bubble sort and any (even undiscovered) algorithm that only exchanges adjacent elements. Consequence: **a subquadratic sort must exchange elements that are far apart** (Shellsort gaps, heap parent/child jumps, quicksort partition swaps, merging).

### 2.4 What the exam asks about insertion sort

- Trace it pass by pass (HW7 7.1); count inversions; say it is stable, in place, O(N^2) worst/average and O(N) best.
- "Running time on all-equal / sorted / reverse input" (7.2: O(N), O(N), O(N^2)).
- "Insertion sort on input where every element is at most k places from its final position": O(Nk) (inversions <= (2k-1)N).

**Check yourself.**
1. How many inversions does `5, 4, 3, 2, 1` have, and what does insertion sort cost on it? <details><summary>Answer</summary>All C(5,2) = 10 pairs are inversions (the maximum N(N-1)/2); insertion sort makes 10 shifts and Theta(N^2) work for general N.</details>
2. Does insertion sort run in O(N) on `2, 1, 4, 3, 6, 5, ...`? <details><summary>Answer</summary>Yes: there are N/2 inversions (each element is 1 away from its place), O(N + I) = O(N).</details>

---

## 3. Selection sort (background, brief)

Pass p = 0 .. N-2: find the minimum of `a[p..N-1]` and swap it into position p. It always scans the whole unsorted part: (N-1) + (N-2) + ... + 1 = N(N-1)/2 comparisons, **Theta(N^2) in the best, average and worst case** (presorted input does not help), but only **N-1 swaps**. In place, **not stable** (`3a, 3b, 1` -> `1, 3b, 3a`). The textbook lists it with bubble sort as a "simple" quadratic sort; Theorem 7.2 is stated for adjacent exchanges, but selection sort is quadratic anyway because of its N(N-1)/2 comparisons.

---

## 4. Mergesort (Textbook 7.6; slides; HW7 7.15, 7.17)

### 4.1 Worked example first: the merge, then the whole sort

**Merge** two sorted runs A = `1 13 24 26` and B = `2 15 27 38` (the book's example): compare the fronts, copy the smaller to the output, advance that pointer. Comparisons: 1 vs 2 -> 1; 13 vs 2 -> 2; 13 vs 15 -> 13; 24 vs 15 -> 15; 24 vs 27 -> 24; 26 vs 27 -> 26; A is exhausted, so copy `27 38` for free. Output `1 2 13 15 24 26 27 38` after **6 comparisons** (at most N-1 = 7). Every comparison places one element, except the last one, which finishes a run and leaves at least two elements to copy.

**Whole sort** of the book's `24, 13, 26, 1, 2, 27, 38, 15`: the recursion finishes the whole left half before touching the right half, so merges happen in this order.

```
merge [24] + [13] -> [13, 24]  (indices 0..1)
    [13 24] 26 1 2 27 38 15
merge [26] + [1] -> [1, 26]  (indices 2..3)
    13 24 [1 26] 2 27 38 15
merge [13, 24] + [1, 26] -> [1, 13, 24, 26]  (indices 0..3)
    [1 13 24 26] 2 27 38 15
merge [2] + [27] -> [2, 27]  (indices 4..5)
    1 13 24 26 [2 27] 38 15
merge [38] + [15] -> [15, 38]  (indices 6..7)
    1 13 24 26 2 27 [15 38]
merge [2, 27] + [15, 38] -> [2, 15, 27, 38]  (indices 4..7)
    1 13 24 26 [2 15 27 38]
merge [1, 13, 24, 26] + [2, 15, 27, 38] -> [1, 2, 13, 15, 24, 26, 27, 38]  (indices 0..7)
    [1 2 13 15 24 26 27 38]

final: 1,2,13,15,24,26,27,38
```

An odd size (center = (0+8)/2 = 4, so the left half is indices 0..4 and gets the extra element) - note the merge order: left half first, merge of [27,38]+[43] before [3,9]:

```
merge [38] + [27] -> [27, 38]  (indices 0..1)
    [27 38] 43 3 9 82 10 5 1
merge [27, 38] + [43] -> [27, 38, 43]  (indices 0..2)
    [27 38 43] 3 9 82 10 5 1
merge [3] + [9] -> [3, 9]  (indices 3..4)
    27 38 43 [3 9] 82 10 5 1
merge [27, 38, 43] + [3, 9] -> [3, 9, 27, 38, 43]  (indices 0..4)
    [3 9 27 38 43] 82 10 5 1
merge [82] + [10] -> [10, 82]  (indices 5..6)
    3 9 27 38 43 [10 82] 5 1
merge [5] + [1] -> [1, 5]  (indices 7..8)
    3 9 27 38 43 10 82 [1 5]
merge [10, 82] + [1, 5] -> [1, 5, 10, 82]  (indices 5..8)
    3 9 27 38 43 [1 5 10 82]
merge [3, 9, 27, 38, 43] + [1, 5, 10, 82] -> [1, 3, 5, 9, 10, 27, 38, 43, 82]  (indices 0..8)
    [1 3 5 9 10 27 38 43 82]

final: 1,3,5,9,10,27,38,43,82
```

<!-- HOLD hw7 -->
The HW7 7.15 input:

```
merge [3] + [1] -> [1, 3]  (indices 0..1)
    [1 3] 4 1 5 9 2 6
merge [4] + [1] -> [1, 4]  (indices 2..3)
    1 3 [1 4] 5 9 2 6
merge [1, 3] + [1, 4] -> [1, 1, 3, 4]  (indices 0..3)
    [1 1 3 4] 5 9 2 6
merge [5] + [9] -> [5, 9]  (indices 4..5)
    1 1 3 4 [5 9] 2 6
merge [2] + [6] -> [2, 6]  (indices 6..7)
    1 1 3 4 5 9 [2 6]
merge [5, 9] + [2, 6] -> [2, 5, 6, 9]  (indices 4..7)
    1 1 3 4 [2 5 6 9]
merge [1, 1, 3, 4] + [2, 5, 6, 9] -> [1, 1, 2, 3, 4, 5, 6, 9]  (indices 0..7)
    [1 1 2 3 4 5 6 9]

final: 1,1,2,3,4,5,6,9
```

<!-- /HOLD -->

N elements need exactly **N - 1 merges** (every merge reduces the number of runs by one, starting from N runs of size 1).

### 4.2 The code (Figures 7.11 and 7.12) line by line

```cpp
template <typename Comparable>
void mergeSort( vector<Comparable> & a )                         // driver
{
    vector<Comparable> tmpArray( a.size( ) );                     // ONE temp array, allocated once
    mergeSort( a, tmpArray, 0, a.size( ) - 1 );
}

template <typename Comparable>
void mergeSort( vector<Comparable> & a, vector<Comparable> & tmpArray, int left, int right )
{
    if( left < right )                                            // size >= 2
    {
        int center = ( left + right ) / 2;                        // left half gets the extra element
        mergeSort( a, tmpArray, left, center );                   // sort left half
        mergeSort( a, tmpArray, center + 1, right );              // sort right half
        merge( a, tmpArray, left, center + 1, right );            // combine: O(N)
    }
}

template <typename Comparable>
void merge( vector<Comparable> & a, vector<Comparable> & tmpArray,
            int leftPos, int rightPos, int rightEnd )
{
    int leftEnd = rightPos - 1;
    int tmpPos = leftPos;
    int numElements = rightEnd - leftPos + 1;

    while( leftPos <= leftEnd && rightPos <= rightEnd )           // main loop
        if( a[ leftPos ] <= a[ rightPos ] )                       // <= : ties come from the LEFT run => stable
            tmpArray[ tmpPos++ ] = std::move( a[ leftPos++ ] );
        else
            tmpArray[ tmpPos++ ] = std::move( a[ rightPos++ ] );

    while( leftPos <= leftEnd )                                   // copy rest of first half
        tmpArray[ tmpPos++ ] = std::move( a[ leftPos++ ] );
    while( rightPos <= rightEnd )                                 // copy rest of right half
        tmpArray[ tmpPos++ ] = std::move( a[ rightPos++ ] );

    for( int i = 0; i < numElements; ++i, --rightEnd )            // copy back
        a[ rightEnd ] = std::move( tmpArray[ rightEnd ] );
}
```

Why only one temp array: `merge` is the *last* statement of `mergeSort`, so only one merge is active at a time; a local temp array per call would cost log N arrays. Cost of `merge`: every element is copied twice (to `tmpArray` and back) and at most N-1 comparisons are made: **Theta(N) time, Theta(N) extra space**.

### 4.3 Analysis (slides "Mergesort Analysis", Textbook 7.6.1) - learn the telescoping

T(1) = 1, T(N) = 2T(N/2) + N for N a power of 2. **Divide by N** (this is what makes it telescope):

T(N)/N = T(N/2)/(N/2) + 1, and likewise T(N/2)/(N/2) = T(N/4)/(N/4) + 1, ..., T(2)/2 = T(1)/1 + 1.

Add all log N equations: every middle term appears on both sides and cancels, leaving **T(N)/N = T(1) + log N**, so **T(N) = N log N + N = Theta(N log N)**. Second method (substitution): T(N) = 2T(N/2) + N = 4T(N/4) + 2N = 8T(N/8) + 3N = ... = 2^k T(N/2^k) + kN, with k = log N: N T(1) + N log N.

- The recursion never looks at the data, and `merge` always touches all N elements, so mergesort is **Theta(N log N) in the best, average and worst case** (HW7 7.17: sorted, reverse and random input are all Theta(N log N); only the *number of comparisons* differs by a constant: about (N/2) log N for sorted/reverse, about N log N - 1.25N random, at most N log N - N + 1).
- **Stable** (the `<=`), **O(N) extra space** (not in place).
- Good for **linked lists**: merging relinks nodes, so no random access and no extra array (O(1) extra space for the merge); `std::list::sort` is a mergesort. Poor fit for arrays when memory is tight.
- Uses the fewest comparisons of the popular sorts (Java's generic sort is a mergesort); C++ historically prefers quicksort because moving large objects is expensive (C++11 move semantics change that trade-off).

**Check yourself.**
1. Merge `2 5 8 11` with `1 3 4 12 15`: how many comparisons? <details><summary>Answer</summary>7: (2,1) (2,3) (5,3) (5,4) (5,12) (8,12) (11,12); then A is empty and `12 15` is copied without comparisons. Bound N - 1 = 8.</details>
2. How many merges does mergesort do on 9 elements, and what are the halves at the top level? <details><summary>Answer</summary>8 merges (N - 1); halves are indices 0..4 and 5..8.</details>
3. Why does the telescoping proof divide by N first? <details><summary>Answer</summary>So that the coefficient of the recursive term on the right (T(N/2)/(N/2)) matches the left side of the next equation; without it, the terms do not cancel.</details>

---

## 5. The decision-tree lower bound for sorting (Textbook 7.8; slides "A General Lower Bound for Sorting")

**Model.** Any sorting algorithm that learns about the input only by comparing pairs can be drawn as a binary **decision tree**: an internal node is a comparison "a < b?", its two edges are the answers, a leaf is a final sorted order. The number of comparisons on an input = depth of its leaf, so the worst case = depth of the tree. For 3 elements (Figure 7.20) the tree has 6 leaves and depth 3.

Sorting must distinguish all N! orderings, so the tree has **at least N! leaves**.

- **Lemma 1.** A binary tree of depth d has at most 2^d leaves. (Induction: d = 0 has 1 leaf; otherwise the root has two subtrees of depth <= d-1, each with <= 2^(d-1) leaves.)
- **Lemma 2.** A binary tree with L leaves has depth at least ceil(log2 L). (From Lemma 1: L <= 2^d.) E.g. L = 17 -> d >= ceil(4.09) = 5; L = 2^16 -> d >= 16.
- **Theorem 1.** Any comparison sort needs at least **ceil(log2(N!))** comparisons in the worst case.
- **Theorem 2.** ceil(log2 N!) is Omega(N log N): log(N!) = log N + log(N-1) + ... + log 1 >= log N + ... + log(N/2) >= (N/2) log(N/2) = (N/2) log N - N/2.

Values of ceil(log2 N!):

| N | N! | log2(N!) | ceil(log2 N!) |
|---|---|---|---|
| 2 | 2 | 1.00 | **1** |
| 3 | 6 | 2.58 | **3** |
| 4 | 24 | 4.58 | **5** |
| 5 | 120 | 6.91 | **7** |
| 6 | 720 | 9.49 | **10** |
| 7 | 5040 | 12.30 | **13** |
| 8 | 40320 | 15.30 | **16** |
| 9 | 362880 | 18.47 | **19** |
| 10 | 3628800 | 21.79 | **22** |

**Consequences (the slides ask "what does this mean for mergesort, heapsort, quicksort?"):** mergesort and heapsort are **optimal** to within a constant factor (O(N log N) worst case), quicksort is optimal on average (the bound also holds on average, because the average leaf depth of a binary tree with L leaves is >= log L). The bound is *information-theoretic*: it does not give an algorithm and it does **not** apply to counting/bucket/radix sort, which do not just compare. It is also not always achievable exactly: for N = 5 the bound is 7 comparisons but mergesort's worst case is 8.

**Check yourself.** How many comparisons does any comparison sort need in the worst case for 4 elements? <details><summary>Answer</summary>ceil(log2 24) = ceil(4.58) = 5 (mergesort also uses 5 in the worst case for N = 4).</details>

---

## 6. Decision-tree lower bounds for selection (Textbook 7.9; high level only)

- **Finding the minimum needs N - 1 comparisons.** Every non-minimum element must lose at least one comparison; one comparison creates only one loser. A linear scan achieves it, so it is tight.
- **Two smallest elements: N + ceil(log N) - 2** comparisons (tight): knock-out tournament (N - 1 comparisons) then the second smallest must have lost directly to the winner, and the winner played only ceil(log N) games.
- **Median: about 3N/2 - O(log N)** (not tight).
- **k-th smallest: at least N - k + ceil(log C(N, k-1))** comparisons (Theorem 7.9).
- Moral: selection needs only Theta(N) comparisons, strictly less than sorting. This is why heap-based selection O(N + k log N) and quickselect O(N) average (notes 05) exist. (7.10 adversary bounds are **out of scope**.)

---

## 7. Linear-time sorts: bucket / counting sort (slides "Counting Sort"; Textbook 7.11; **light**)

The topics page says counting sort is *not* on the exam, the textbook-chapters page lists it as new material, so know the idea, the O(N + k) bound and when it applies. Radix sort and Shellsort are out.

- **Bucket/counting sort.** Keys are integers in a known range of k values. Make `count[0..k-1] = 0`; for each element `count[key]++` (O(N)); scan `count` in order and write each key `count[key]` times (O(N + k)). Total **O(N + k)**, space O(k). Slides' example: SAT scores 400-1600 in steps of 10: key = (score - 400)/10 in 0..120, so k = 121: sorting 500,000 scores is O(N).
- **Why it does not break Omega(N log N):** it never compares two elements; `count[key]++` is an M-way decision in constant time, which is outside the decision-tree model.
- **Limits:** same as a direct-address table - useless when the range k is huge compared with N (N = 1000 32-bit values: O(N + 2^32)), or keys are not small integers.
- **Hash variation (slides):** count the values in an `unordered_map` (O(N) average), copy the d distinct (value, count) pairs into an array and sort them with a comparison sort (O(d log d)), then expand: **O(N + d log d)** (the slide writes k for the number of unique values: O(n + k log k)). Worst case of the hash makes the counting O(N^2). d constant -> O(N); d = N -> O(N log N), no gain.

---

## 8. External sorting - concepts only (Textbook 7.12)

- **Why new algorithms:** the data does not fit in memory; internal sorts need random access (`a[i]`, `a[2i+1]`, median-of-3), but tapes are sequential and disks have costly seeks. Reading the input is O(N) and slow, so the number of **passes** over the data is what matters.
- **The simple algorithm:** read M records at a time, sort them in memory, write each sorted **run** alternately to two tapes (N/M runs). Then repeatedly **merge** runs pairwise (the mergesort merge: sequential reads/writes only, nearly no memory) onto the other pair of tapes; each pass halves the number of runs: **ceil(log2(N/M)) merge passes** plus the run-construction pass.
- **Multiway merge:** k-way merging cuts the passes to **ceil(log_k(N/M))** (needs 2k tapes). Finding the smallest of the k run fronts uses a **priority queue** (deleteMin, then insert the next record of that run).
- **Polyphase merge** gets by with k + 1 tapes by splitting the runs unevenly (Fibonacci numbers).
- **Replacement selection** builds the runs with a priority queue of M records: output the smallest, read the next record, and if it is not smaller than the one just written it joins the current run. Average run length for random input is **2M** (very long runs for nearly sorted input), so fewer runs and fewer passes.
- Pass counts for 1000 initial runs: 2-way -> 10, 4-way -> 5, 10-way -> 3.

---

## 9. Master tables

### 9.1 Every sort

| Sort | Best | Average | Worst | Extra space | Stable | In place |
|---|---|---|---|---|---|---|
| Insertion | O(N) (presorted); O(N + I) in general | O(N^2) | O(N^2) | O(1) | yes | yes |
| Selection | O(N^2) | O(N^2) | O(N^2) | O(1) | no | yes |
| Mergesort | O(N log N) | O(N log N) | O(N log N) | O(N) arrays; O(1) lists | yes | no |
| Heapsort | O(N log N) | O(N log N) | O(N log N) | O(1) | no | yes |
| Quicksort (median-of-3) | O(N log N) | O(N log N) | **O(N^2)** | O(log N) stack (O(N) worst) | no | yes |
| Introsort (`std::sort`) | O(N log N) | O(N log N) | O(N log N) | O(log N) | no | yes |
| Counting sort (light) | O(N + k) | O(N + k) | O(N + k) | O(k) (+O(N) output) | yes (if implemented so) | no |
| Comparison-sort lower bound | Omega(N log N) comparisons, worst and average | | | | | |

### 9.2 Every fundamental operation

| Operation | Time | One-line reason |
|---|---|---|
| `merge` of two sorted runs, total N | **O(N)** | each element copied once (twice with the copy-back), <= N-1 comparisons |
| one insertion-sort pass at position p | O(1) best, O(p) worst | slides past the larger elements; cost = inversions that a[p] takes part in |
| `partition` of N elements (Hoare) | **O(N)** | i and j sweep the subarray once |
| `buildHeap` | **O(N)** | sum of heights of nodes is O(N), not N log N |
| `deleteMax` / `percolateDown` | **O(log N)** | one root-to-leaf path in a complete tree |
| heapsort total | O(N) + N * O(log N) = O(N log N) | buildHeap, then N deleteMax |
| quickselect | **O(N) average**, O(N^2) worst | one recursive call: N + N/2 + ... |
| heap-based selection of the k-th | O(N + k log N) | buildHeap + k deleteMin |
| counting sort | O(N + k) | one pass over the input, one over the counts |
| `std::sort` / `std::stable_sort` | O(N log N) | introsort / mergesort |
| `std::nth_element` | O(N) average | quickselect |

---

## 10. Traps that cost points

1. **Mergesort's best case is not O(N).** It is Theta(N log N) always (sorted input does not help; only the comparison count changes by a constant).
2. **Insertion sort best case O(N) needs presorted input.** All-equal input is also O(N) because the test is *strict*; a `<=` would make it quadratic and unstable.
3. **Inversions need a[i] > a[j] strictly**; equal elements are not inversions.
4. **Stability:** insertion sort and mergesort yes; selection, quicksort, heapsort no. Say *why* from the code (`<` strict, `<=` in merge).
5. **Mergesort space is O(N)** (the temp array), not O(log N) (that is only the recursion stack). It is "not in place".
6. **Merge order in traces:** depth-first, left half first; the left half gets the extra element for odd sizes; a size-1 subarray is never merged.
7. **Lower bound wording:** Omega(N log N) comparisons for *comparison-based* sorts. Counting sort is O(N + k) and does not contradict it. Do not say "no sort can be faster than N log N".
8. **Decision-tree proof details:** N! leaves, depth >= ceil(log2 N!), and log2 N! >= (N/2) log2(N/2). Mention Lemma 1 (at most 2^d leaves).
9. **Average inversions is N(N-1)/4, maximum N(N-1)/2** - do not mix them up.
10. **Hash variation:** the sort is on the d *distinct* values: O(N + d log d), average case for the hash.

---

## 11. What the exam asks (and how it will look)

- **Trace** insertion sort (passes) or mergesort (order of merges) on a short array - 6-8 points.
- **Complexity of a sort and of its fundamental operation:** "give the complexity of merge / partition / buildHeap / deleteMax and of the whole sort", with a one-line reason each.
- **Short proof or explanation:** inversions and the Omega(N^2) adjacent-swap bound; decision-tree lower bound; mergesort recurrence by telescoping.
- **"Which sort would you use and why?"** (nearly sorted -> insertion; linked list -> mergesort; guaranteed worst case in place -> heapsort/introsort; stability -> stable_sort; small integer keys -> counting sort).
- **Cumulative design/analysis** (about half the exam): any sort is a building block - e.g. "sort then merge" for a sorted list plus a few extras, "sort strings: O(L N log N)", or the counting/hash variation. Always name the cost of each STL call.

**Mini-quiz.**
1. State the complexity of insertion sort in terms of N and the number of inversions I. <details><summary>Answer</summary>O(N + I).</details>
2. Why can no adjacent-swap sort beat N^2 on average? <details><summary>Answer</summary>The average input has N(N-1)/4 inversions and one adjacent swap removes exactly one.</details>
3. Give the recurrence, solution and extra space of mergesort. <details><summary>Answer</summary>T(N) = 2T(N/2) + N, T(N) = N log N + N = Theta(N log N); O(N) extra space.</details>
4. What is the lower bound on comparisons to sort 5 elements? <details><summary>Answer</summary>ceil(log2 120) = ceil(6.91) = 7.</details>
5. List the stable sorts among insertion, selection, merge, quick, heap. <details><summary>Answer</summary>Insertion and merge.</details>

(More practice: `bank/sortbasics.json`; traces on demand: `python tools/study.py sort random insertion` / `mergesort`.)
