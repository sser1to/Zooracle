using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class questions
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public string name { get; set; }

        public int? question_type_id { get; set; }
        [ForeignKey("question_type_id")]
        public question_types question_type { get; set; }

        // Списки
        public List<question_answer> question_answer { get; set; } = new();
        public List<test_questions> test_questions { get; set; } = new();
    }
}
