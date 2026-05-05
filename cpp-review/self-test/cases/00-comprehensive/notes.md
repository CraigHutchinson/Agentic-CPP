# Case 00: Comprehensive

One header/implementation pair with eleven deliberate defects spanning most check
categories. Run this case first to get an end-to-end cost baseline.

## Defect map

| ID  | Defect | Location | Check | Expected tier |
| --- | --- | --- | --- | --- |
| E1  | Missing class docblock on `TokenDispatcher` | `input.h:11` | Stranger Q1 (DOC-COMMENT) | SHOULD |
| E2  | Raw pointer `m_Queue` with no ownership annotation | `input.h:26` | Stranger Q5 (DOC-COMMENT) | SHOULD |
| E3  | Boolean selector params `async`, `validate` on `Dispatch` | `input.h:15` | L2 API smell | SHOULD |
| E4  | `std::pair<bool, Token>` return on `TryDequeue` | `input.h:21` | L2 API smell | SHOULD |
| E5  | Missing `[[nodiscard]]` on `IsEmpty()` | `input.h:18` | L3 modernisation | SHOULD |
| E6  | Unscoped `enum DispatchMode` | `input.h:32` | L3 modernisation | SHOULD |
| E7  | `typedef` alias `TokenList` | `input.h:40` | L3 modernisation | SHOULD |
| E8  | C-style cast `(Token*)&t` | `input.cpp:37` | L3 modernisation | **MUST** |
| E9  | Index-based loop replaceable with range-for | `input.cpp:41` | L3 modernisation | SHOULD |
| E10 | `CompareIgnoreCase` reinvents existing project utility | `input.cpp:8` | Reinvention check | **MUST** |
| E11 | `s_Queue` file-static with `ENABLE_UNIT_TESTS_WITH_FAKES` bypass | `input.cpp:20` | Testability | **MUST** |

## Must-not-fire

`GetQueue()` returns `*s_Queue`, which would dereference null if called before
`s_Queue` is set. The reviewer must NOT raise a null-guard finding at every call
site -- that responsibility belongs at the initialization site where `s_Queue` is
assigned. The input-source check suppresses this.
