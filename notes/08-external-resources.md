# 08 - External resources linked in the Exam 2 slides and homework

All of these open in the study browser (`study view <url>`). They come from the Hashing, C++ STL, Leetcode Hashing,
Heaps and Sorting slides and from HW5–HW7.

## Visualizations (watch the textbook algorithm, then check it against `--show`)

| Link | Use it for | Caveat |
|---|---|---|
| https://www.cs.usfca.edu/~galles/visualization/ComparisonSort.html | insertion, merge, heap, quick sort animations (Sorting slides) | its quicksort partition is **not** the textbook 7.7.2 one, so use `study sort partition ... --show` for exam traces |
| https://www.cs.usfca.edu/~galles/visualization/Heap.html | min-heap insert / removeSmallest | it is 1-indexed like the textbook but doesn't show index 0 as the temp |
| https://www.cs.usfca.edu/~galles/visualization/OpenHash.html | separate chaining | may insert at the **front** of the list; the textbook (and HW5) append at the **end**, so trust the engine |
| https://www.cs.usfca.edu/~galles/visualization/ClosedHash.html | linear / quadratic / double hashing | its second hash function may differ from hash2(x) = R − (x mod R); check before trusting it |
| https://opendsa-server.cs.vt.edu/embed/quicksortAV | quicksort visualization (Sorting slides) | different partition variant; trust the engine for the exam |

## C++ reference pages (complexities to cite in analysis answers)

| Page | What to read |
|---|---|
| https://cplusplus.com/reference/unordered_map/unordered_map/ | member list; "Complexity" sections: average constant, worst linear |
| https://cplusplus.com/reference/unordered_map/unordered_map/operator[]/ | creates a default element if the key is missing (HW5 hint) |
| https://cplusplus.com/reference/unordered_set/unordered_set/ | same costs for sets |
| https://cplusplus.com/reference/set/set/ and https://cplusplus.com/reference/set/set/lower_bound/ | O(log n); range search with lower_bound / upper_bound |
| https://cplusplus.com/reference/queue/priority_queue/ | max-heap by default; `priority_queue<int, vector<int>, greater<int>>` for a min-heap |
| https://cplusplus.com/reference/algorithm/make_heap/ · https://cplusplus.com/reference/algorithm/pop_heap/ | HW7 C (myHeapSort): make_heap up to 3n comparisons, pop_heap up to 2 log n |
| https://cplusplus.com/reference/algorithm/sort/ · https://cplusplus.com/reference/algorithm/stable_sort/ | O(n log n); stable_sort keeps equal keys in order |
| https://cplusplus.com/reference/string/string/substr/ | HW5 Part 3b (Repeated DNA Sequences) |

## LeetCode problems (slides + homework)

| Problem | Where | Notes / bank |
|---|---|---|
| https://leetcode.com/problems/contains-duplicate/ | Leetcode Hashing slide | `notes/02` |
| https://leetcode.com/problems/two-sum/ | slide + Hashing slides "classic problem" | naive O(n²) / sort O(n log n) / hash O(n) avg |
| https://leetcode.com/problems/intersection-of-two-linked-lists/ | slide | hash set of nodes |
| https://leetcode.com/problems/valid-anagram/ | slide | counting map |
| https://leetcode.com/problems/longest-substring-without-repeating-characters/ | slide | map of last position |
| https://leetcode.com/problems/contains-duplicate-ii/ | slide + HW5 Part 3a | map value → last index |
| https://leetcode.com/problems/contains-duplicate-iii/ | slide + HW4 | sliding-window `set` + lower_bound, O(n log k) |
| https://leetcode.com/problems/repeated-dna-sequences/ | HW5 Part 3b | O(n) with unordered_map, O(n log n) with map |
| https://leetcode.com/problems/kth-largest-element-in-a-stream/ | HW6 Q3 | size-k min-heap |

## Background reading

| Link | Why |
|---|---|
| https://en.wikipedia.org/wiki/Lazy_deletion | HW5 5.7b answer cites it |
| https://www.javatpoint.com/counting-sort | Sorting slides, counting sort (light topic) |
| https://stackoverflow.com/questions/8269916/what-is-sliding-window-algorithm-examples | HW4 sliding-window hint |
