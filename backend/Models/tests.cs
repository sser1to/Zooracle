using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class tests
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public string name { get; set; }

        // Списки
        public List<test_questions> test_questions { get; set; } = new();
        public List<test_score> test_score { get; set; } = new();
    }
}
